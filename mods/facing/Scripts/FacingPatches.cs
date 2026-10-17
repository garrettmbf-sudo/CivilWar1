// Harmony patches. Signatures verified against decompiled Assembly-CSharp.dll
// (Template-Mod-Harmony / Example-Mod-Harmony Libraries, sha256 495f9af5a582fee9...,
// MultiplayerManager.VERSION "8.4.14"). Line numbers are from ILSpy 8.2 output.
using System;
using HarmonyLib;
using HexOfSteelFacing.Core;
using UnityEngine;

namespace HexOfSteelFacing
{
    // UnitGO.cs:4141  public void RotateUnit(TileGO p_departureTileGO, TileGO p_arrivalTileGO)
    // Called per path step in the move coroutine (UnitGO.cs:1664) and on multiplayer replay
    // (MultiplayerManager.cs:1793). Vanilla only sets E/W for LEFT_RIGHT units and returns early
    // for NONE units, so for our units we compute the 6-way facing ourselves.
    [HarmonyPatch(typeof(UnitGO), nameof(UnitGO.RotateUnit), new Type[] { typeof(TileGO), typeof(TileGO) })]
    static class Patch_RotateUnit
    {
        static bool Prefix(UnitGO __instance, TileGO p_departureTileGO, TileGO p_arrivalTileGO)
        {
            try
            {
                if (!FacingRuntime.IsManaged(__instance)) return true;
                if (p_departureTileGO == null || p_arrivalTileGO == null || p_departureTileGO == p_arrivalTileGO)
                {
                    __instance.SetUnitRotation(); // UnitGO.cs:5743 calls RotateUnit(tileGO, tileGO) just to redraw
                    return false;
                }
                if (FacingRuntime.Delta(p_departureTileGO.tile, p_arrivalTileGO.tile, out double dx, out double dy))
                    FacingRuntime.SetFacing(__instance, FacingMath.DirectionOf(dx, dy));
                return false;
            }
            catch (Exception e) { Debug.LogError("[Facing] RotateUnit: " + e); return true; }
        }
    }

    // UnitGO.cs:4001  public void RotateAttackedUnit(UnitGO p_unitGOtoRotate, UnitGO p_refUnitGO)
    // Callers: AttackUnit (UnitGO.cs:2586, rotates the attacker toward the target), support fire
    // (3459), Retaliate (3666, rotates the defender toward the attacker), defensive fire (5814),
    // MultiplayerManager.cs:1128. Rule: only units the active player controls may turn
    // (TurnManager.currPlayer.CanControlUnitsOf, Player.cs:1760). Enemy units keep their facing.
    [HarmonyPatch(typeof(UnitGO), nameof(UnitGO.RotateAttackedUnit), new Type[] { typeof(UnitGO), typeof(UnitGO) })]
    static class Patch_RotateAttackedUnit
    {
        static bool Prefix(UnitGO p_unitGOtoRotate, UnitGO p_refUnitGO)
        {
            try
            {
                if (!FacingRuntime.IsManaged(p_unitGOtoRotate)) return true;
                Player cur = TurnManager.currPlayer;
                bool mayTurn = cur != null && p_unitGOtoRotate.unit.OwnerPlayer != null
                               && cur.CanControlUnitsOf(p_unitGOtoRotate.unit.OwnerPlayer);
                if (mayTurn && p_refUnitGO != null)
                    FacingRuntime.FaceToward(p_unitGOtoRotate, FacingRuntime.TileOf(p_refUnitGO));
                return false;
            }
            catch (Exception e) { Debug.LogError("[Facing] RotateAttackedUnit: " + e); return true; }
        }
    }

    // UnitGO.cs:6954  public void SetUnitRotation()
    // Vanilla: NATO => rotation 0; LEFT_RIGHT => Y-flip 0/180 (and coerces facing to WEST);
    // ALL => Z-rotation of unitSprite. For our units: keep only the E/W flip, never rotate the
    // figure, never overwrite the stored 6-way facing, and draw the chevron.
    [HarmonyPatch(typeof(UnitGO), nameof(UnitGO.SetUnitRotation))]
    static class Patch_SetUnitRotation
    {
        static bool Prefix(UnitGO __instance)
        {
            try
            {
                if (!FacingRuntime.IsManaged(__instance) || __instance.unitSprite == null) return true;
                Transform t = ((Component)__instance.unitSprite).transform;
                if (UIManager.isNATO || __instance.unit.AllowedRotation == AllowedRotations.NONE)
                {
                    if (UIManager.isNATO) t.rotation = Quaternion.Euler(0f, 0f, 0f);
                }
                else
                {
                    bool? east = FacingMath.FacesEast(FacingRuntime.GetFacing(__instance.unit));
                    if (east.HasValue) t.rotation = Quaternion.Euler(0f, east.Value ? 180f : 0f, 0f); // vanilla: EAST=180, WEST=0
                    else
                    {
                        // N or S: keep the current left/right flip, drop any Z rotation.
                        float y = Mathf.Abs(Mathf.DeltaAngle(t.eulerAngles.y, 180f)) < 90f ? 180f : 0f;
                        t.rotation = Quaternion.Euler(0f, y, 0f);
                    }
                }
                FacingRuntime.UpdateChevron(__instance);
                return false;
            }
            catch (Exception e) { Debug.LogError("[Facing] SetUnitRotation: " + e); return true; }
        }
    }

    // Unit.cs:1517  public int GetPotentialDamage(UnitGO p_targetUnitGO, bool p_isRetaliation, bool p_isSupportiveFire)
    // Both the result and the public field Unit.FinalDamage (Unit.cs:101) must change: the real attack
    // (UnitGO.AttackUnit 2631 -> Attack 3219 "CurrHP -= unit.FinalDamage"), retaliation (3659/3671),
    // support fire (3372/3461) and the combat preview (UnitGO.cs:4964-4992) all read FinalDamage,
    // while the AI ranks targets with the return value (AI.CheckForAttack, 26 call sites in AI.cs).
    // Squad of Steel patches this same method (Scripts/Combat/SquadOfSteelCombatPatches.cs).
    [HarmonyPatch(typeof(Unit), nameof(Unit.GetPotentialDamage), new Type[] { typeof(UnitGO), typeof(bool), typeof(bool) })]
    static class Patch_GetPotentialDamage
    {
        static void Postfix(Unit __instance, UnitGO p_targetUnitGO, bool p_isRetaliation, bool p_isSupportiveFire, ref int __result)
        {
            try
            {
                var cfg = FacingMod.Config;
                if (!cfg.enabled || __result <= 0 || p_targetUnitGO == null) return;
                // Retaliation hits the attacker, which vanilla AttackUnit has already turned to face its
                // target (UnitGO.cs:2586 runs before GetPotentialDamage at 2631), so it is always frontal.
                // Skipping it also keeps the preview's retaliation number equal to the real one.
                if (p_isRetaliation) return;
                if (p_isSupportiveFire && !cfg.applyToSupportiveFire) return;
                if (__instance.Type == "Plane" || __instance.Type == "Boat") return; // air/naval fire ignores facing
                if (!FacingRuntime.IsManaged(p_targetUnitGO)) return;
                UnitGO attackerGO = __instance.unitGO;
                if (!FacingRuntime.Delta(FacingRuntime.TileOf(p_targetUnitGO), FacingRuntime.TileOf(attackerGO), out double dx, out double dy)) return;
                Arc arc = FacingMath.Classify(FacingRuntime.GetFacing(p_targetUnitGO.unit), dx, dy);
                double m = arc == Arc.Front ? cfg.frontMultiplier : arc == Arc.Flank ? cfg.flankMultiplier : cfg.rearMultiplier;
                int nd = FacingMath.ApplyMultiplier(__result, m);
                __result = nd;
                __instance.FinalDamage = nd;
            }
            catch (Exception e) { Debug.LogError("[Facing] GetPotentialDamage: " + e); }
        }
    }

    // TurnManager.cs:262  public void NextTurn(bool p_sendRPC)
    // At prefix time TurnManager.currPlayer is still the player ending the turn. For AI players,
    // turn every unit toward its nearest enemy (Player.ListOfUnits, Unit.unitGO). Runs from the same
    // state on every client, so it is deterministic.
    [HarmonyPatch(typeof(TurnManager), nameof(TurnManager.NextTurn), new Type[] { typeof(bool) })]
    static class Patch_NextTurn
    {
        static void Prefix()
        {
            try
            {
                var cfg = FacingMod.Config;
                Player p = TurnManager.currPlayer;
                if (!cfg.enabled || !cfg.aiRefaceEnabled || p == null || !p.IsComputer || p.ListOfUnits == null) return;
                foreach (Unit u in p.ListOfUnits.ToArray())
                {
                    if (u == null || u.IsReserve || !FacingRuntime.IsManaged(u)) continue;
                    UnitGO go = u.unitGO;
                    if (go == null || go.tileGO == null) continue;
                    UnitGO enemy = FacingRuntime.NearestEnemy(go, cfg.aiRefaceRadius);
                    if (enemy != null) FacingRuntime.FaceToward(go, FacingRuntime.TileOf(enemy));
                }
            }
            catch (Exception e) { Debug.LogError("[Facing] NextTurn: " + e); }
        }
    }
}
