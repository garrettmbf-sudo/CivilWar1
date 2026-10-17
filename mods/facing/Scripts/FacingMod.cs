// Entry point. Same shape as the official Template-Mod-Harmony (Scripts/TemplateMod.cs):
// a GameModification subclass constructed by Mod.LoadAssemblies with (Mod) and initialised
// through OnModInitialization, patching with Harmony.PatchAll().
using HarmonyLib;
using UnityEngine;

namespace HexOfSteelFacing
{
    public class FacingMod : GameModification
    {
        public const string Version = "0.1.0";
        public static FacingConfig Config = new FacingConfig();
        public static FacingMod Instance;
        Harmony _harmony;
        GameObject _input;

        public FacingMod(Mod p_mod) : base(p_mod)
        {
            Log("Registering facing mod " + Version);
        }

        public override void OnModInitialization(Mod p_mod)
        {
            Instance = this;
            Config = FacingConfig.Load(p_mod?.InstallLocation, s => Log(s));
            _harmony = new Harmony("com.hexofsteel." + Mod.Name);
            _harmony.PatchAll(typeof(FacingMod).Assembly);
            Log("Patched methods: " + string.Join(", ", System.Linq.Enumerable.Select(_harmony.GetPatchedMethods(), m => m.DeclaringType.Name + "." + m.Name)));
            if (Config.turnInPlaceEnabled)
            {
                _input = new GameObject("HexOfSteelFacing.Input");
                Object.DontDestroyOnLoad(_input);
                _input.AddComponent<TurnInPlaceInput>();
            }
        }

        public override void OnModUnloaded()
        {
            _harmony?.UnpatchAll(_harmony.Id);
            if (_input != null) Object.Destroy(_input);
            Log("Unloaded");
        }

        public static void Info(string s) { Instance?.Log(s); }
    }
}
