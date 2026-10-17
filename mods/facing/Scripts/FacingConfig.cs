using System;
using System.IO;
using Newtonsoft.Json;
using UnityEngine;

namespace HexOfSteelFacing
{
    /// <summary>Settings read from FacingConfig.json in the mod's root folder (Mod.InstallLocation).</summary>
    public class FacingConfig
    {
        public bool enabled = true;
        public double frontMultiplier = 1.0;
        public double flankMultiplier = 1.25;
        public double rearMultiplier = 1.5;
        /// <summary>Also apply the multiplier to supportive (defensive/artillery support) fire.</summary>
        public bool applyToSupportiveFire = true;
        /// <summary>Facing used for units saved with the old EAST/WEST values (0..5 = N, NE, SE, S, SW, NW).</summary>
        public int legacyEastFacing = 1;
        public int legacyWestFacing = 5;
        public bool showChevron = true;
        public float chevronDistance = 1.9f;
        public float chevronScale = 0.7f;
        public string chevronColorHex = "#F2C14E";
        public bool turnInPlaceEnabled = true;
        public int turnInPlaceMPCost = 1;
        /// <summary>UnityEngine.KeyCode names.</summary>
        public string rotateClockwiseKey = "Period";
        public string rotateCounterClockwiseKey = "Comma";
        public bool aiRefaceEnabled = true;
        public int aiRefaceRadius = 6;

        public const string FileName = "FacingConfig.json";

        public static FacingConfig Load(string modFolder, Action<string> log)
        {
            try
            {
                string path = Path.Combine(modFolder ?? "", FileName);
                if (File.Exists(path))
                {
                    var cfg = JsonConvert.DeserializeObject<FacingConfig>(File.ReadAllText(path)) ?? new FacingConfig();
                    log?.Invoke($"Loaded {path}: front {cfg.frontMultiplier} flank {cfg.flankMultiplier} rear {cfg.rearMultiplier}");
                    return cfg;
                }
                log?.Invoke($"{path} not found, using defaults");
            }
            catch (Exception e)
            {
                log?.Invoke("Config error, using defaults: " + e.Message);
            }
            return new FacingConfig();
        }

        public Color ChevronColor()
        {
            Color c;
            return ColorUtility.TryParseHtmlString(chevronColorHex, out c) ? c : new Color(0.95f, 0.76f, 0.31f);
        }
    }
}
