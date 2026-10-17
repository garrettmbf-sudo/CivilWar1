// Turn in place: '.' turns the selected unit clockwise, ',' counter-clockwise, costing
// FacingConfig.turnInPlaceMPCost movement points (Unit.CurrMP, byte, Unit.cs:232).
// Keys are read through reflection on UnityEngine.Input, like Squad of Steel's
// SquadOfSteelKeybindHandler, so no InputLegacyModule reference is needed at compile time.
// Disabled in realtime multiplayer: a local facing change has no RPC and would desync.
// PBEM/hotseat are fine, since the facing is saved in the .sav (Unit.FacingRotation).
using System;
using System.Reflection;
using HexOfSteelFacing.Core;
using UnityEngine;

namespace HexOfSteelFacing
{
    public class TurnInPlaceInput : MonoBehaviour
    {
        static MethodInfo _getKeyDown;
        static bool _init;
        KeyCode _cw, _ccw;

        void Start()
        {
            _cw = Parse(FacingMod.Config.rotateClockwiseKey, KeyCode.Period);
            _ccw = Parse(FacingMod.Config.rotateCounterClockwiseKey, KeyCode.Comma);
        }

        static KeyCode Parse(string s, KeyCode d)
        {
            try { return (KeyCode)Enum.Parse(typeof(KeyCode), s, true); } catch { return d; }
        }

        static bool KeyDown(KeyCode k)
        {
            if (!_init)
            {
                _init = true;
                Type t = Type.GetType("UnityEngine.Input, UnityEngine.InputLegacyModule") ?? Type.GetType("UnityEngine.Input, UnityEngine");
                _getKeyDown = t?.GetMethod("GetKeyDown", new[] { typeof(KeyCode) });
                if (_getKeyDown == null) Debug.LogWarning("[Facing] UnityEngine.Input.GetKeyDown not found; turn in place disabled");
            }
            return _getKeyDown != null && (bool)_getKeyDown.Invoke(null, new object[] { k });
        }

        void Update()
        {
            try
            {
                var cfg = FacingMod.Config;
                if (!cfg.enabled || !cfg.turnInPlaceEnabled) return;
                int step = KeyDown(_cw) ? 1 : KeyDown(_ccw) ? -1 : 0;
                if (step == 0) return;
                if (GameData.Instance == null || TurnManager.currPlayer == null || TurnManager.currPlayer.IsComputer) return;
                if (MultiplayerManager.IsRealtimeMultiplayer()) return;
                UnitGO go = MapGO.selectedUnitGO;
                if (!FacingRuntime.IsManaged(go) || go.unit.OwnerPlayer == null) return;
                if (!TurnManager.currPlayer.CanControlUnitsOf(go.unit.OwnerPlayer)) return;
                int cost = Math.Max(0, cfg.turnInPlaceMPCost);
                if (go.unit.CurrMP < cost) return;
                go.unit.CurrMP = (byte)(go.unit.CurrMP - cost);
                FacingRuntime.SetFacing(go, FacingMath.Mod6(FacingRuntime.GetFacing(go.unit) + step));
                try { go.ShowSelectedUnitStats(); go.ShowPotentialPaths(); } catch (Exception e) { Debug.LogWarning("[Facing] refresh: " + e.Message); }
            }
            catch (Exception e) { Debug.LogError("[Facing] TurnInPlace: " + e); }
        }
    }
}
