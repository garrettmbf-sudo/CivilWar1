// Game-facing helpers. Every member used here was checked against the decompiled
// Assembly-CSharp.dll (game 8.4.14, sha256 495f9af5...). File:line refer to the ILSpy 8.2 output.
using System;
using System.Collections.Generic;
using HexOfSteelFacing.Core;
using UnityEngine;

namespace HexOfSteelFacing
{
    public static class FacingRuntime
    {
        /// <summary>
        /// Units that get 6-way facing: living, mobile ground units that are not on a boat.
        /// Unit.Type strings "Plane"/"Boat" are used throughout the game (e.g. Unit.ApplyEncirclementDamageModifier).
        /// MaxMP > 0 excludes static units (bunkers, mines, depots), as CalculateEncirclement does.
        /// </summary>
        public static bool IsManaged(Unit u)
        {
            if (u == null || !FacingMod.Config.enabled) return false;
            if (u.IsDead || u.IsMine || u.IsOnBoat) return false;
            if (u.Type == "Plane" || u.Type == "Boat") return false;
            return u.MaxMP > 0;
        }

        public static bool IsManaged(UnitGO go) => go != null && go.unit != null && IsManaged(go.unit);

        public static int GetFacing(Unit u)
            => FacingMath.ToFacing6((byte)u.FacingRotation, FacingMod.Config.legacyEastFacing, FacingMod.Config.legacyWestFacing);

        public static void SetFacing(UnitGO go, int facing6)
        {
            go.unit.FacingRotation = (FacingRotations)FacingMath.ToEnum(facing6);
            go.SetUnitRotation(); // our prefix redraws flip + chevron
        }

        /// <summary>Vector from tile a to tile b in game world units, from Tile.PosX/PosY (deterministic, no transforms).</summary>
        public static bool Delta(Tile from, Tile to, out double dx, out double dy)
        {
            dx = dy = 0;
            if (from == null || to == null) return false;
            FacingMath.GameCenter(from.PosX, from.PosY, out double ax, out double ay);
            FacingMath.GameCenter(to.PosX, to.PosY, out double bx, out double by);
            dx = bx - ax; dy = by - ay;
            return !(dx == 0 && dy == 0);
        }

        public static Tile TileOf(UnitGO go) => go?.tileGO?.tile;

        /// <summary>Nearest enemy ground unit within radius (Utils.GetAllTilesInRadiusAround, TileGO.groundUnitGO, Player.IsAtWarWith).</summary>
        public static UnitGO NearestEnemy(UnitGO go, int radius)
        {
            Tile t = TileOf(go);
            if (t == null || go.unit.OwnerPlayer == null) return null;
            List<Tile> tiles = Utils.GetAllTilesInRadiusAround(t, radius);
            if (tiles == null) return null;
            var dx = new List<double>(); var dy = new List<double>(); var ids = new List<int>(); var gos = new List<UnitGO>();
            foreach (Tile other in tiles)
            {
                UnitGO e = other?.tileGO?.groundUnitGO;
                if (e == null || e == go || e.unit == null || e.unit.IsDead || e.unit.OwnerPlayer == null) continue;
                if (!go.unit.OwnerPlayer.IsAtWarWith(e.unit.OwnerPlayer)) continue;
                if (Delta(t, other, out double x, out double y)) { dx.Add(x); dy.Add(y); ids.Add(e.unit.ID); gos.Add(e); }
            }
            int i = FacingMath.NearestIndex(dx, dy, ids);
            return i < 0 ? null : gos[i];
        }

        public static void FaceToward(UnitGO go, Tile target)
        {
            if (Delta(TileOf(go), target, out double dx, out double dy))
                SetFacing(go, FacingMath.DirectionOf(dx, dy));
        }

        // ---------------- chevron ----------------
        const string ChevronName = "HexOfSteelFacing.Chevron";
        static Sprite _chevronSprite;

        static Sprite ChevronSprite()
        {
            if (_chevronSprite != null) return _chevronSprite;
            const int n = 64;
            var tex = new Texture2D(n, n, TextureFormat.RGBA32, false);
            var clear = new Color(0, 0, 0, 0);
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                {
                    // Upward-pointing chevron: inside a triangle, outside a smaller notch.
                    float u = (x - n / 2f) / (n / 2f), v = y / (float)n;  // u -1..1, v 0..1 (bottom to top)
                    bool inOuter = v <= 1f - Mathf.Abs(u) && v >= 0.05f;
                    bool inNotch = v <= 0.55f - Mathf.Abs(u) * 0.55f;
                    bool fill = inOuter && !inNotch;
                    bool edge = fill && (v > 0.93f - Mathf.Abs(u) || v < 0.12f || v < 0.62f - Mathf.Abs(u) * 0.55f);
                    tex.SetPixel(x, y, fill ? (edge ? new Color(0.1f, 0.1f, 0.1f, 1f) : Color.white) : clear);
                }
            tex.Apply();
            tex.filterMode = FilterMode.Bilinear;
            _chevronSprite = Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);
            return _chevronSprite;
        }

        public static void UpdateChevron(UnitGO go)
        {
            if (!FacingMod.Config.showChevron || go == null) return;
            Transform root = ((Component)go).transform;
            Transform ch = root.Find(ChevronName);
            if (!IsManaged(go))
            {
                if (ch != null) ch.gameObject.SetActive(false);
                return;
            }
            SpriteRenderer sr;
            if (ch == null)
            {
                var obj = new GameObject(ChevronName);
                obj.transform.SetParent(root, false);
                sr = obj.AddComponent<SpriteRenderer>();
                sr.sprite = ChevronSprite();
                sr.color = FacingMod.Config.ChevronColor();
                ch = obj.transform;
            }
            else sr = ch.GetComponent<SpriteRenderer>();
            if (go.unitSprite != null && sr != null)
            {
                sr.sortingLayerID = go.unitSprite.sortingLayerID;
                sr.sortingOrder = go.unitSprite.sortingOrder + 5;
            }
            int f = GetFacing(go.unit);
            float ang = (float)FacingMath.FacingAngleDeg(f) * Mathf.Deg2Rad;
            float d = FacingMod.Config.chevronDistance;
            ch.localPosition = new Vector3(Mathf.Cos(ang) * d, Mathf.Sin(ang) * d, -0.05f);
            ch.localRotation = Quaternion.Euler(0f, 0f, (float)FacingMath.FacingAngleDeg(f) - 90f);
            float s = FacingMod.Config.chevronScale;
            ch.localScale = new Vector3(s, s, 1f);
            ch.gameObject.SetActive(true);
        }
    }
}
