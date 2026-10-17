using System;
using System.IO;
using System.Linq;
using System.Text.Json;
using HexOfSteelFacing.Core;
using Xunit;

public class FacingMathTests
{
    static JsonElement Fixture()
    {
        var p = Path.Combine(AppContext.BaseDirectory, "fixtures", "hex_utils_neighbors.json");
        return JsonDocument.Parse(File.ReadAllText(p)).RootElement;
    }

    [Fact]
    public void CenterMatchesHexUtils_OddQ()
    {
        // hex_utils.hex_center: x = col*sqrt(3)/2, y = row + 0.5*(col&1)  (odd columns shifted north)
        foreach (var c in Fixture().GetProperty("cases").EnumerateArray())
        {
            FacingMath.Center(c.GetProperty("col").GetInt32(), c.GetProperty("row").GetInt32(), 1, Math.Sqrt(3) / 2, 1.0, out double x, out double y);
            Assert.Equal(c.GetProperty("cx").GetDouble(), x, 9);
            Assert.Equal(c.GetProperty("cy").GetDouble(), y, 9);
        }
    }

    [Fact]
    public void DirectionOfNeighbourEqualsHexUtilsPort()
    {
        int n = 0;
        foreach (var c in Fixture().GetProperty("cases").EnumerateArray())
        {
            double dx = c.GetProperty("nx").GetDouble() - c.GetProperty("cx").GetDouble();
            double dy = c.GetProperty("ny").GetDouble() - c.GetProperty("cy").GetDouble();
            Assert.Equal(c.GetProperty("port").GetInt32(), FacingMath.DirectionOf(dx, dy));
            n++;
        }
        Assert.Equal(288, n);
    }

    // Game geometry (MapGO): EVEN columns shifted north, pitch 4.42 x 5.1.
    [Theory]
    [InlineData(4, 4, 4, 5, FacingMath.N)]
    [InlineData(4, 4, 5, 5, FacingMath.NE)]   // even col 4 sits half a row north: odd col 5, row+1 is NE
    [InlineData(4, 4, 5, 4, FacingMath.SE)]   // ... and odd col 5, same row is SE
    [InlineData(4, 4, 4, 3, FacingMath.S)]
    [InlineData(4, 4, 3, 4, FacingMath.SW)]
    [InlineData(4, 4, 3, 5, FacingMath.NW)]
    [InlineData(5, 4, 6, 4, FacingMath.NE)]   // odd col 5 sits low: even col 6, same row is NE
    [InlineData(5, 4, 6, 3, FacingMath.SE)]
    [InlineData(5, 4, 4, 3, FacingMath.SW)]
    [InlineData(5, 4, 4, 4, FacingMath.NW)]
    public void GameGeometryNeighbours(int c, int r, int nc, int nr, int expected)
    {
        FacingMath.GameCenter(c, r, out double ax, out double ay);
        FacingMath.GameCenter(nc, nr, out double bx, out double by);
        Assert.Equal(expected, FacingMath.DirectionOf(bx - ax, by - ay));
    }

    [Fact]
    public void GameGridIsNearlyRegular()
    {
        // 4.42 / 2.55 = 1.7333 vs sqrt(3) = 1.7321: NE neighbour sits at ~29.98 deg, well inside its sector.
        FacingMath.GameCenter(4, 4, out double ax, out double ay);
        FacingMath.GameCenter(5, 5, out double bx, out double by);
        double ang = Math.Atan2(by - ay, bx - ax) * 180 / Math.PI;
        Assert.InRange(ang, 29.9, 30.1);
    }

    [Theory]
    // defender facing N (0); attacker in each adjacent direction
    [InlineData(0, 0, Arc.Front)]
    [InlineData(0, 1, Arc.Flank)]
    [InlineData(0, 5, Arc.Flank)]
    [InlineData(0, 2, Arc.Rear)]
    [InlineData(0, 3, Arc.Rear)]
    [InlineData(0, 4, Arc.Rear)]
    // every facing, relative side r = attacker direction - facing
    [InlineData(2, 2, Arc.Front)]
    [InlineData(2, 3, Arc.Flank)]
    [InlineData(2, 1, Arc.Flank)]
    [InlineData(2, 5, Arc.Rear)]
    [InlineData(4, 1, Arc.Rear)]
    [InlineData(5, 0, Arc.Flank)]
    public void ClassifyAdjacent(int facing, int attackerDir, Arc expected)
    {
        double a = FacingMath.FacingAngleDeg(attackerDir) * Math.PI / 180;
        Assert.Equal(expected, FacingMath.Classify(facing, Math.Cos(a), Math.Sin(a)));
    }

    [Fact]
    public void AllSixFacingsTimesSixSides()
    {
        for (int f = 0; f < 6; f++)
            for (int d = 0; d < 6; d++)
            {
                int rel = FacingMath.Mod6(d - f);
                var exp = rel == 0 ? Arc.Front : (rel == 1 || rel == 5) ? Arc.Flank : Arc.Rear;
                FacingMath.GameCenter(10, 10, out double x0, out double y0);
                // build the real neighbour in game geometry for direction d
                var nb = new[] { (0, 1), (1, 1), (1, 0), (0, -1), (-1, 0), (-1, 1) }; // even column 10 (shifted north)
                FacingMath.GameCenter(10 + nb[d].Item1, 10 + nb[d].Item2, out double x1, out double y1);
                Assert.Equal(d, FacingMath.DirectionOf(x1 - x0, y1 - y0));
                Assert.Equal(exp, FacingMath.Classify(f, x1 - x0, y1 - y0));
            }
    }

    [Fact]
    public void RangedTieGoesToDefender()
    {
        // Exactly 30 deg off the facing: front, not flank. Exactly 90: flank, not rear.
        double a = (90 - 30) * Math.PI / 180;
        Assert.Equal(Arc.Front, FacingMath.Classify(0, Math.Cos(a), Math.Sin(a)));
        Assert.Equal(Arc.Flank, FacingMath.Classify(0, 1, 0));
        Assert.Equal(Arc.Flank, FacingMath.Classify(0, -1, 0));
    }

    [Theory]
    [InlineData(20, 1.0, 20)]
    [InlineData(20, 1.25, 25)]
    [InlineData(20, 1.5, 30)]
    [InlineData(10, 1.25, 12)]   // 12.5 -> 12 (to even), same rule as the game's modifiers
    [InlineData(14, 1.25, 18)]   // 17.5 -> 18
    [InlineData(7, 1.5, 10)]     // 10.5 -> 10
    [InlineData(0, 1.5, 0)]
    public void MultiplierRounding(int dmg, double m, int expected)
        => Assert.Equal(expected, FacingMath.ApplyMultiplier(dmg, m));

    [Fact]
    public void EnumRoundTrip()
    {
        for (int f = 0; f < 6; f++) Assert.Equal(f, FacingMath.ToFacing6(FacingMath.ToEnum(f)));
        Assert.Equal(1, FacingMath.ToFacing6(FacingMath.FR_EAST));
        Assert.Equal(5, FacingMath.ToFacing6(FacingMath.FR_WEST));
        Assert.Equal(new byte[] { 2, 4, 6, 3, 7, 5 }, Enumerable.Range(0, 6).Select(FacingMath.ToEnum).ToArray());
    }

    [Fact]
    public void NearestIsDeterministic()
    {
        Assert.Equal(2, FacingMath.NearestIndex(new[] { 3.0, 1.0, 1.0 }, new[] { 0.0, 0.0, 0.0 }, new[] { 5, 9, 2 }));
        Assert.Equal(-1, FacingMath.NearestIndex(new double[0], new double[0], new int[0]));
    }

    [Fact]
    public void FlipFromFacing()
    {
        Assert.True(FacingMath.FacesEast(FacingMath.NE));
        Assert.True(FacingMath.FacesEast(FacingMath.SE));
        Assert.False(FacingMath.FacesEast(FacingMath.SW));
        Assert.False(FacingMath.FacesEast(FacingMath.NW));
        Assert.Null(FacingMath.FacesEast(FacingMath.N));
        Assert.Null(FacingMath.FacesEast(FacingMath.S));
    }
}
