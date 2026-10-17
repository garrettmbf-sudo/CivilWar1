// Pure facing math for the Hex of Steel facing mod. No Unity or game types here, so it
// can be unit-tested on plain .NET. All game-specific constants cite the decompiled
// Assembly-CSharp.dll (Example-Mod-Harmony / Template-Mod-Harmony, sha256 495f9af5a582fee9...,
// MultiplayerManager.VERSION = "8.4.14").
using System;
using System.Collections.Generic;

namespace HexOfSteelFacing.Core
{
    /// <summary>Which side of the defender the attack comes from.</summary>
    public enum Arc { Front = 0, Flank = 1, Rear = 2 }

    public static class FacingMath
    {
        // MapGO tile placement (MapGO.cs, scenario load loop):
        //   odd column:  position = (col * 4.42, row * 5.1)
        //   even column: position = (col * 4.42, row * 5.1 + 2.55)
        // World +y is north on screen (UnitGO.RotateUnit: arrival.y > departure.y => NORTH).
        public const double GameColPitch = 4.42;
        public const double GameRowPitch = 5.1;
        /// <summary>Parity of the columns that the game shifts half a row north (0 = even).</summary>
        public const int GameNorthShiftedParity = 0;

        // Facing index 0..5 = N, NE, SE, S, SW, NW (same as src/hex_utils.py ports).
        public const int N = 0, NE = 1, SE = 2, S = 3, SW = 4, NW = 5;

        // FacingRotations enum byte values (FacingRotations.cs):
        // WEST=0, EAST=1, NORTH=2, SOUTH=3, NORTH_EAST=4, NORTH_WEST=5, SOUTH_EAST=6, SOUTH_WEST=7
        public const byte FR_WEST = 0, FR_EAST = 1, FR_NORTH = 2, FR_SOUTH = 3,
                          FR_NORTH_EAST = 4, FR_NORTH_WEST = 5, FR_SOUTH_EAST = 6, FR_SOUTH_WEST = 7;

        static readonly byte[] Facing6ToEnum = { FR_NORTH, FR_NORTH_EAST, FR_SOUTH_EAST, FR_SOUTH, FR_SOUTH_WEST, FR_NORTH_WEST };

        public static byte ToEnum(int facing6) => Facing6ToEnum[Mod6(facing6)];

        /// <summary>True when the stored enum value is one of the 6 hex directions.</summary>
        public static bool IsHexFacing(byte enumValue) => enumValue >= FR_NORTH && enumValue <= FR_SOUTH_WEST;

        /// <summary>Enum value to 0..5. Legacy WEST/EAST (left-right units, default 0) use the fallbacks.</summary>
        public static int ToFacing6(byte enumValue, int legacyEast = NE, int legacyWest = NW)
        {
            switch (enumValue)
            {
                case FR_NORTH: return N;
                case FR_NORTH_EAST: return NE;
                case FR_SOUTH_EAST: return SE;
                case FR_SOUTH: return S;
                case FR_SOUTH_WEST: return SW;
                case FR_NORTH_WEST: return NW;
                case FR_EAST: return Mod6(legacyEast);
                default: return Mod6(legacyWest); // FR_WEST and anything unexpected
            }
        }

        public static int Mod6(int v) => ((v % 6) + 6) % 6;

        /// <summary>Centre of an offset hex in a north-up frame.</summary>
        public static void Center(int col, int row, int northShiftedParity, double colPitch, double rowPitch,
                                  out double x, out double y)
        {
            x = col * colPitch;
            y = row * rowPitch + ((Math.Abs(col) % 2) == northShiftedParity ? rowPitch / 2.0 : 0.0);
        }

        /// <summary>Centre of game tile (PosX, PosY), in world units, same formula as MapGO.</summary>
        public static void GameCenter(int posX, int posY, out double x, out double y)
            => Center(posX, posY, GameNorthShiftedParity, GameColPitch, GameRowPitch, out x, out y);

        /// <summary>Angle in degrees (counter-clockwise from east) of the centre of facing 0..5.</summary>
        public static double FacingAngleDeg(int facing6) => 90.0 - 60.0 * Mod6(facing6);

        /// <summary>
        /// Hex direction 0..5 of the vector (dx, dy), using 60-degree sectors centred on N, NE, SE, S, SW, NW.
        /// Exact sector boundaries go clockwise (to the higher index); this is deterministic.
        /// </summary>
        public static int DirectionOf(double dx, double dy)
        {
            if (dx == 0 && dy == 0) return -1;
            double ang = Math.Atan2(dy, dx) * 180.0 / Math.PI;      // -180..180, CCW from east
            double cw = 90.0 - ang;                                  // clockwise from north
            int sector = (int)Math.Floor((cw + 30.0) / 60.0);
            return Mod6(sector);
        }

        /// <summary>Absolute angle 0..180 between the defender's facing and the direction to the attacker.</summary>
        public static double RelativeAngleDeg(int defenderFacing6, double dxToAttacker, double dyToAttacker)
        {
            double ang = Math.Atan2(dyToAttacker, dxToAttacker) * 180.0 / Math.PI;
            double d = ang - FacingAngleDeg(defenderFacing6);
            d = ((d % 360.0) + 540.0) % 360.0 - 180.0;
            return Math.Abs(d);
        }

        /// <summary>
        /// Front: within 30 deg of facing (the hexside faced). Flank: up to 90 deg (the two adjacent hexsides).
        /// Rear: beyond 90 deg (the three back hexsides). Ties go to the defender (the less damaging arc).
        /// </summary>
        public static Arc Classify(int defenderFacing6, double dxToAttacker, double dyToAttacker)
        {
            const double eps = 1e-6;
            double rel = RelativeAngleDeg(defenderFacing6, dxToAttacker, dyToAttacker);
            if (rel <= 30.0 + eps) return Arc.Front;
            if (rel <= 90.0 + eps) return Arc.Flank;
            return Arc.Rear;
        }

        /// <summary>Same rounding as the game's damage modifiers (Math.Round, MidpointRounding.ToEven).</summary>
        public static int ApplyMultiplier(int damage, double multiplier)
        {
            if (damage <= 0) return damage;
            int r = (int)Math.Round(damage * multiplier, MidpointRounding.ToEven);
            return r < 0 ? 0 : r;
        }

        /// <summary>Index of the nearest candidate (squared distance, then lowest id). -1 if none.</summary>
        public static int NearestIndex(IList<double> dx, IList<double> dy, IList<int> ids)
        {
            int best = -1; double bestD = double.MaxValue; int bestId = int.MaxValue;
            for (int i = 0; i < dx.Count; i++)
            {
                double d = dx[i] * dx[i] + dy[i] * dy[i];
                if (d < bestD - 1e-9 || (Math.Abs(d - bestD) <= 1e-9 && ids[i] < bestId))
                { best = i; bestD = d; bestId = ids[i]; }
            }
            return best;
        }

        /// <summary>East/west sprite flip from a 6-way facing: true = east, false = west, null = keep (N/S).</summary>
        public static bool? FacesEast(int facing6)
        {
            switch (Mod6(facing6))
            {
                case NE: case SE: return true;
                case SW: case NW: return false;
                default: return null;
            }
        }
    }
}
