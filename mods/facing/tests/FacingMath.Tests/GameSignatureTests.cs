// Verifies, against the real Assembly-CSharp.dll (compile-only copy in .hos-libs/), that every
// member the mod patches or touches exists with the exact signature. Skips if the DLLs are absent.
using System;
using System.IO;
using System.Linq;
using System.Reflection;
using Xunit;

public class GameSignatureTests
{
    static string Libs() =>
        typeof(GameSignatureTests).Assembly.GetCustomAttributes<AssemblyMetadataAttribute>().First(a => a.Key == "HoSLibs").Value;

    static MetadataLoadContext Ctx()
    {
        var libs = Libs();
        var paths = Directory.GetFiles(libs, "*.dll").Concat(Directory.GetFiles(Path.GetDirectoryName(typeof(object).Assembly.Location), "*.dll"));
        return new MetadataLoadContext(new PathAssemblyResolver(paths), "mscorlib");
    }

    static bool Have() => File.Exists(Path.Combine(Libs(), "Assembly-CSharp.dll"));

    static MethodInfo M(Assembly a, string type, string name, params string[] ps)
    {
        var t = a.GetType(type, true);
        return t.GetMethods(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static | BindingFlags.DeclaredOnly)
                .SingleOrDefault(m => m.Name == name && m.GetParameters().Select(p => p.ParameterType.Name).SequenceEqual(ps));
    }

    [Fact]
    public void PatchedMethodsExistWithExactSignatures()
    {
        if (!Have()) return;
        using var ctx = Ctx();
        var a = ctx.LoadFromAssemblyPath(Path.Combine(Libs(), "Assembly-CSharp.dll"));
        var m1 = M(a, "UnitGO", "RotateUnit", "TileGO", "TileGO");
        Assert.NotNull(m1); Assert.True(m1.IsPublic); Assert.Equal("Void", m1.ReturnType.Name);
        Assert.Equal(new[] { "p_departureTileGO", "p_arrivalTileGO" }, m1.GetParameters().Select(p => p.Name));
        var m2 = M(a, "UnitGO", "RotateAttackedUnit", "UnitGO", "UnitGO");
        Assert.NotNull(m2); Assert.True(m2.IsPublic);
        Assert.Equal(new[] { "p_unitGOtoRotate", "p_refUnitGO" }, m2.GetParameters().Select(p => p.Name));
        var m3 = M(a, "UnitGO", "SetUnitRotation");
        Assert.NotNull(m3); Assert.True(m3.IsPublic);
        var m4 = M(a, "Unit", "GetPotentialDamage", "UnitGO", "Boolean", "Boolean");
        Assert.NotNull(m4); Assert.Equal("Int32", m4.ReturnType.Name);
        Assert.Equal(new[] { "p_targetUnitGO", "p_isRetaliation", "p_isSupportiveFire" }, m4.GetParameters().Select(p => p.Name));
        var m5 = M(a, "TurnManager", "NextTurn", "Boolean");
        Assert.NotNull(m5); Assert.Equal("p_sendRPC", m5.GetParameters()[0].Name);
        Assert.NotNull(M(a, "UnitGO", "ShowSelectedUnitStats"));
        Assert.NotNull(M(a, "UnitGO", "ShowPotentialPaths"));
        Assert.NotNull(M(a, "Player", "CanControlUnitsOf", "Player"));
        Assert.NotNull(M(a, "Player", "IsAtWarWith", "Player"));
        Assert.NotNull(M(a, "Utils", "GetAllTilesInRadiusAround", "Tile", "Int32"));
        Assert.NotNull(M(a, "MultiplayerManager", "IsRealtimeMultiplayer"));
        Assert.NotNull(M(a, "GameModification", "OnModInitialization", "Mod"));
    }

    [Fact]
    public void FieldsAndPropertiesUsedExist()
    {
        if (!Have()) return;
        using var ctx = Ctx();
        var a = ctx.LoadFromAssemblyPath(Path.Combine(Libs(), "Assembly-CSharp.dll"));
        var unit = a.GetType("Unit", true);
        Assert.Equal("FacingRotations", unit.GetProperty("FacingRotation").PropertyType.Name);
        Assert.Equal("AllowedRotations", unit.GetProperty("AllowedRotation").PropertyType.Name);
        Assert.Equal("Byte", unit.GetProperty("CurrMP").PropertyType.Name);
        Assert.Equal("Byte", unit.GetProperty("MaxMP").PropertyType.Name);
        Assert.Equal("Int32", unit.GetField("FinalDamage").FieldType.Name);
        Assert.Equal("UnitGO", unit.GetField("unitGO").FieldType.Name);
        foreach (var p in new[] { "IsDead", "IsMine", "IsOnBoat", "IsReserve" }) Assert.Equal("Boolean", unit.GetProperty(p).PropertyType.Name);
        Assert.Equal("Int32", unit.GetProperty("ID").PropertyType.Name);
        var ugo = a.GetType("UnitGO", true);
        Assert.Equal("SpriteRenderer", ugo.GetField("unitSprite").FieldType.Name);
        Assert.Equal("TileGO", ugo.GetField("tileGO").FieldType.Name);
        Assert.Equal("Tile", a.GetType("TileGO", true).GetField("tile").FieldType.Name);
        Assert.Equal("UnitGO", a.GetType("TileGO", true).GetField("groundUnitGO").FieldType.Name);
        Assert.Equal("Int16", a.GetType("Tile", true).GetField("PosX").FieldType.Name);
        var tm = a.GetType("TurnManager", true);
        Assert.True(tm.GetField("currPlayer").IsStatic);
        Assert.True(a.GetType("MapGO", true).GetField("selectedUnitGO").IsStatic);
        Assert.True(a.GetType("UIManager", true).GetField("isNATO").IsStatic);
        var fr = a.GetType("FacingRotations", true);
        Assert.Equal(new[] { "WEST", "EAST", "NORTH", "SOUTH", "NORTH_EAST", "NORTH_WEST", "SOUTH_EAST", "SOUTH_WEST" },
            fr.GetFields(BindingFlags.Public | BindingFlags.Static).OrderBy(f => Convert.ToInt32(f.GetRawConstantValue())).Select(f => f.Name));
        var mm = a.GetType("MultiplayerManager", true).GetField("VERSION");
        Assert.Equal("8.4.14", mm.GetRawConstantValue());
    }
}
