# CivilWar1 — Shenandoah Valley 1862 Tile Catalog

**Design status: Historically plausible classes, not yet a verified in-game tile pack.** Forty tile definitions cover March–May 1862 at 250 yards/hex. Names, placements, bridges, depots, hospitals and military earthworks require date-specific source control. Values below are deliberate balance proposals, not verified native Hex of Steel serialization fields.

## Compatibility and source discipline

- **Positive defense modifier:** `+N%` in this catalog is the *intended percentage reduction of incoming damage* on the defending tile, consistent with the official manual's illustrative +30% reduction. No historic defense number is sourced from the period; all are design choices. Native hilltop +15% defender damage effect, if retained, is separate and must not be mistaken for defense reduction.
- **Attack penalty:** Values are proposed *attacker outgoing-damage penalties*. The ordinary native tile editor may not provide a separate attack penalty field; implement via Harmony only after inspecting the running assembly, otherwise leave 0%. Do not double-count penalties with defense.
- **Movement cost:** Listed MP corresponds to game's tile movement-point cost (sometimes informally called AP); native examples are road 1, clear 2, forest 3. `BLOCK` requires an actual movement-class rule—not a numeric MP. Road/river/rail overlaps must preserve each underlying network independently.
- **Production & victory points:** Default zero production for ordinary 250-yard terrain. Values 1 for a mill/depot are optional scenario economy targets, not automatic game income. VPs are **scenario assignments**, not inherent to an isolated art tile; type may be regular/secondary/major according to map objectives.
- **Overlay-first architecture:** One underlying natural terrain and elevation layer per hex; independent edge-port networks for road, rail, river, wall, fence; separate structure and season overlays. When a river and road meet, an automatically rendered crossing **must not** imply a functioning bridge/ford.
- **Cartographic status:** The 1862 Hotchkiss survey is an outstanding source for named farmsteads, relief, roads and streams, but it was compiled during the campaign; do not equate every mapped military structure or bridge state to the situation on March 1. Cross Keys is June 8, outside a March–May base snapshot.

## Six-edge adjacency & sprite standard

Flat-top horizontal top/bottom, points left and right. Ports **0=N**, **1=NE**, **2=SE**, **3=S**, **4=SW**, **5=NW**. On contiguous adjacent hexes, a required port must match the neighbor's reciprocal port `(d+3) mod 6`. For roads, rivers and railways, annotate each sprite with an exact set of port numbers, line endpoint pixel offsets and local elevation at ports. A sprite selected only by neighbor tile *category* may look adjacent without actually connecting. Use shared *world-coordinate* height samples at every border vertex to avoid the 3-D platform look.

**Bundle art acceptance:** seamless exact edge-to-edge seams at game scale; no baked full-hex platform shadows; vegetation edges and color noise world-coordinate consistent; transparent alpha outside the silhouette; roads/rails/water enter only approved edge centers; all bridge and route masks reciprocal; audit rotation rules for Hex of Steel's actual atlas before naming final native tiles.

## Tile catalog


### 01. Open Wheat Field — `T_OPEN_WHEAT`

**Category:** Field; **render layer:** `field`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Rolling shallow furrows of overwintered wheat in muted green rows between tan earth; wet clay between rows in March, thicker growth by May. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Infantry open to fire; field boundaries belong to an independent fence-edge layer.

**1862 authenticity:** Wheat cultivation and patchwork open agricultural land are characteristic of the 1862 Valley. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 02. Ploughed Field — `T_PLOUGHED`

**Category:** Field; **render layer:** `field`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Rich dark-brown turned soil, narrow raised furrows, remnants of maize stalks; shallow standing water in furrow bottoms. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** Rain-soaked furrows slow guns and wagons; speed penalty beyond tile MP is conditional.

**1862 authenticity:** Period agricultural tillage, cornfields and cleared cropland are consistent with contemporary Valley maps. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 03. Broom Straw Field — `T_BROOM`

**Category:** Field; **render layer:** `field`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Ochre broom-sedge stalks and winter-brown hummocks waving over gently rolling abandoned or rough pasture; scattered old fence posts. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +5%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Low concealment for prone infantry only; no ballistic protection. Camouflage requires optional Harmony rule.

**1862 authenticity:** Old-field broom sedge and uncultivated grassland are plausible historical Appalachian vegetation. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 04. Pasture — `T_PASTURE`

**Category:** Field; **render layer:** `field`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Short uneven brown-and-faint-green grazed grass, bare patches around troughs, occasional cedars and limestone fragments. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Open ground; livestock props purely decorative; keep rail fences on shared hex edges.

**1862 authenticity:** Grazed fields and fences were widespread on 1860s Valley farms. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 05. Orchard — `T_ORCHARD`

**Category:** Orchard; **render layer:** `wood`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. An irregular but planted grid of leafless apple and peach trees casting narrow shadows; wet leaf litter, pale grass and a few fallen branches. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** Obstructs direct line of sight lightly; civilian orchard rows should not entirely block artillery LOS.

**1862 authenticity:** Orchards are mapped or documented around many antebellum Valley farmsteads. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 06. Oak-Hickory Woods (Leafless) — `T_OAK_BARE`

**Category:** Woods; **render layer:** `wood`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Dense interwoven gray limbs with glimpses of russet leaf litter, damp trunks, rock fragments, no summer canopy. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** Reduce sight lines; no full foliage concealment in March.

**1862 authenticity:** Deciduous upland woods dominated this part of the Valley before leaf-out. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 07. Oak-Hickory Woods (Leafing) — `T_OAK_LEAF`

**Category:** Woods; **render layer:** `wood`; **season:** April–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Same hills and tree skeletons as bare tile, but with translucent pale leaf buds and restrained May canopy; no fully mature midsummer foliage. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +20%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** May variant only; heavier visibility penalty than bare woods.

**1862 authenticity:** The same 1862 woodlots progressively leafed out in April and May; not new locations. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 08. Pine Woods — `T_PINE`

**Category:** Woods; **render layer:** `wood`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Steeply viewed evergreen conical pines with interspersed dead hardwoods, rusty pine-needle ground, deep muted green shadows. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +25%; attack penalty -10%; movement 3 MP; production 0; VP No.

**Special rules:** Dense sight obstruction; gun teams slowed.

**1862 authenticity:** Native pines and mixed evergreen woodlands existed on appropriate slopes and sandy ground. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 09. Cedar Thicket — `T_CEDAR`

**Category:** Woods; **render layer:** `wood`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Irregular dark eastern redcedar crowns packed closely together with exposed cedar-red trunks, limestone outcrops and sparse winter grass. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +25%; attack penalty -10%; movement 4 MP; production 0; VP No.

**Special rules:** Concealment high; dismounted passage difficult; guns need route.

**1862 authenticity:** Eastern redcedar thickets are historically plausible in old fields and rocky limestone ground. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 10. Riparian Woods — `T_RIPARIAN`

**Category:** Woods; **render layer:** `waterwood`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Bare sycamores with white peeling limbs, willow and walnut silhouettes along wet eroding creek banks; dark driftwood accumulations. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +20%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** Banks limit guns; line of sight constrained by trees and channel depth.

**1862 authenticity:** Streamside sycamore, willow and walnut grew along Shenandoah tributaries. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 11. Marsh / Wet Meadow — `T_MARSH`

**Category:** Wetland; **render layer:** `wet`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Shallow slate-brown pools between compressed tawny sedges, cattails, matted reeds and small isolated hummocks. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty -10%; movement 4 MP; production 0; VP No.

**Special rules:** Artillery and wagons cannot cross saturated ground without a verified causeway; terrain-class restriction requires engine validation.

**1862 authenticity:** Flood-prone meadows existed in river bottoms; place only where period terrain supports them. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 12. Creek Bottom — `T_CREEK`

**Category:** Water; **render layer:** `river`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. A narrow, turbid run winding through low muddy banks, gravel pockets and unleafed sycamores; channel enters at defined edge ports. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty -5%; movement 4 MP; production 0; VP No.

**Special rules:** Crossable only where depth permits; model creek bank separately from channel; scenario water level can close crossings.

**1862 authenticity:** Numerous tributary creeks appear on period Valley surveys. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 13. River — `T_RIVER`

**Category:** Water; **render layer:** `river`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Broad opaque brown-blue channel with swift eddies, cut banks and bits of driftwood; North or South Fork identity stored in data, not baked on the tile. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement BLOCK MP; production 0; VP No.

**Special rules:** River obstruction: non-engineer crossing forbidden except approved bridge/ford/ferry; require native FilterRiver audit.

**1862 authenticity:** North Fork and South Fork Shenandoah are principal 1862 geographic barriers. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 14. Ford — `T_FORD`

**Category:** Crossing; **render layer:** `cross`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Shallow riffles, broad pebble bar and braided wagon ruts descending both muddy banks; exact edges follow water and road port masks. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty -10%; movement 3 MP; production 0; VP Optional: crossing.

**Special rules:** Pass only if historically attested and water level below threshold; no automatic ford from route overlap. Requires test/Harmony.

**1862 authenticity:** Only named and source-verified 1862 fords may be placed; a generic sprite does not prove location. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 15. Bridge — `T_BRIDGE`

**Category:** Crossing; **render layer:** `cross`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Narrow wooden deck and simple braced timbers spanning a high spring stream, with stone or timber abutments embedded in natural banks. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty 0%; movement 1 MP; production 0; VP Optional: crossing.

**Special rules:** Use verified native bridge tile and bridge-destroyed state; bridge +10% proposed, native exact value must be checked.

**1862 authenticity:** Wooden and stone river/creek crossings existed, but material and precise 1862 sites require source checks. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 16. Stone Wall — `T_STONE_WALL`

**Category:** Boundary; **render layer:** `fence`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Low irregular fieldstone wall, slightly moss-darkened, snaking along one or more hex edges with matched end caps and bends. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +25%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Overlay on base terrain; benefit only to adjacent defending side; exact directional cover needs Harmony.

**1862 authenticity:** Dry-laid limestone walls existed in Valley farms and were important battlefield cover. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 17. Rail Fence — `T_RAIL_FENCE`

**Category:** Boundary; **render layer:** `fence`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Weathered zigzag split-rail fence on a shared hex edge, brown wood with broken posts and muddy footprints. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Directional low cover, minor delay to movement; visually continuous across multiple fields.

**1862 authenticity:** Worm/split rail fences were ordinary antebellum agricultural boundaries. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 18. Valley Pike — `T_VALLEY_PIKE`

**Category:** Road; **render layer:** `road`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Compacted pale-gray macadam strip with drainage ditches, rust-colored roadside mud and occasional crushed stone repairs; edge-matched route. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement 1 MP; production 0; VP Optional: strategic road junction.

**Special rules:** Road grants cost 1 only where connected across traversed edges; underlying terrain remains independent.

**1862 authenticity:** The Valley Turnpike was a documented macadamized north–south military road in 1862. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 19. Dirt Road — `T_DIRT_ROAD`

**Category:** Road; **render layer:** `road`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Twin brown wagon ruts with deeply impressed hoofprints, muddy shoulders, drainage puddles and dry tufts of winter grass. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** March rain can raise cost to 3; dry weather 2; pass across matching edge ports only.

**1862 authenticity:** Unimproved wagon roads and farm roads are recorded throughout period Valley maps. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 20. Railroad — `T_RAILROAD`

**Category:** Rail; **render layer:** `rail`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Single early iron-rail line on closely spaced wooden cross-ties and sparse earth/gravel ballast, slightly raised across wet ground. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement 2 MP; production 0; VP Optional: junction.

**Special rules:** Route overlay; rail transport requires verified railroad tile, track continuity and native train mechanics.

**1862 authenticity:** The Manassas Gap and Virginia Central rail corridors existed by 1862; exact segment status varies and must be dated. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 21. Toll Gate — `T_TOLL_GATE`

**Category:** Infrastructure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Simple timber tollbar and small gatekeeper shelter beside the light gravel Valley Turnpike; open gate and two wagon tracks. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +5%; attack penalty 0%; movement 1 MP; production 0; VP Optional: local objective.

**Special rules:** Landmark overlay; no implicit military blockade or toll mechanic.

**1862 authenticity:** Toll collection infrastructure belonged to antebellum turnpikes; specific tollhouse sites must be documented. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 22. Mill — `T_MILL`

**Category:** Infrastructure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Water-powered stone or frame gristmill beside a millrace and wheel, flour sacks, water chute and damp lime-washed stones. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty -5%; movement 2 MP; production 1; VP Optional: supply objective.

**Special rules:** Food/supply node only when scenario enables; wheel and race are overlays, never an unverified dam crossing.

**1862 authenticity:** Gristmills and millraces were important prewar Valley industrial features; site-specific existence is required. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 23. Depot — `T_DEPOT`

**Category:** Infrastructure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Low wood freight depot with a roofed platform, short siding, timber ties, freight crates and a period water tank if documented. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty 0%; movement 2 MP; production 1; VP Optional: rail/supply objective.

**Special rules:** Rail node; production 1 only if working 1862 station is confirmed, no trains without connected track.

**1862 authenticity:** Period rail depots served railroad communities; only lines and stations operational by campaign date qualify. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 24. Farmstead — `T_FARM`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Period brick, limestone, or log dwelling with shingle roof, single chimney, muddy yard and small detached kitchen and outbuilding. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty -5%; movement 2 MP; production 0; VP Optional: scenario headquarters.

**Special rules:** Farm complex overlay; no automatic income unless assigned a documented supply role.

**1862 authenticity:** Small antebellum farm complexes are extensively recorded on period Hotchkiss maps. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 25. Bank Barn — `T_BANK_BARN`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Large two-level timber-over-stone barn backed into a hillside, raised bank entrance and small forebay; graying roof shingles. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty -5%; movement 2 MP; production 0; VP No.

**Special rules:** Local hard cover; construct on height-adjusted foundation, not a flat slab against ridge.

**1862 authenticity:** Bank barns are a documented regional barn type, particularly in the German farming communities. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 26. Church — `T_CHURCH`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Modest brick, limestone, or timber church with pitched roof, small belfry or steeple and adjacent enclosure; not every church gets a cemetery. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +20%; attack penalty -5%; movement 2 MP; production 0; VP Optional: village.

**Special rules:** Shelter/landmark; church can become a hospital only with date-specific scenario evidence.

**1862 authenticity:** Lutheran, German Reformed, Presbyterian and other church buildings stood in Valley settlements by 1862. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 27. Courthouse — `T_COURTHOUSE`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Historic county court building with masonry walls, cupola or portico only where the actual courthouse supports it; open yard. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +20%; attack penalty 0%; movement 2 MP; production 0; VP Optional: major town.

**Special rules:** Unique civic objective. Architecture must be town-specific, not universal Greek Revival.

**1862 authenticity:** County courthouses existed in Winchester, Woodstock, Harrisonburg, Staunton and other towns, but designs varied. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 28. Tavern / Hotel — `T_TAVERN`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Two-story frame or brick inn with timber porch, stableyard, hitching rail, unpainted mud road and glass-window reflections. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty -5%; movement 2 MP; production 0; VP Optional: town.

**Special rules:** May serve headquarters or hospital only with evidence; no abstract rest bonus without scripting.

**1862 authenticity:** Taverns, inns and hotels served prewar trade and travelers on the Valley roads. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 29. Blacksmith Shop — `T_SMITH`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Small log or frame forge with lean-to, soot-stained stone chimney, cooling tub, coal pile and iron-rimmed wagon wheel. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Repair/refit possible only via scenario-specific support mechanic; decorative by default.

**1862 authenticity:** Village and farm blacksmiths serviced horses, tools and wagons in 1862. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 30. Store — `T_STORE`

**Category:** Structure; **render layer:** `place`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Small merchant storefront of aged wood or brick with modest porch, shuttered windows, barrels and crates; no modern signage. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty 0%; movement 2 MP; production 0; VP Optional: local supply.

**Special rules:** Optional supply cache; normal production 0.

**1862 authenticity:** General stores were documented in Valley villages and market towns. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 31. Earthwork — `T_EARTHWORK`

**Category:** Military; **render layer:** `military`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Freshly cut brown earth parapet and shallow ditch reinforced with rough timber, tufts of tan grass and brush abatis. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +30%; attack penalty 0%; movement 3 MP; production 0; VP Optional: fortification objective.

**Special rules:** Built-state overlay only; initial 1862 presence must be confirmed, directional cover needs Harmony.

**1862 authenticity:** Field trenches and earthworks were constructed by soldiers during campaign; vary by date and side. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 32. Camp — `T_CAMP`

**Category:** Military; **render layer:** `military`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Grouped off-white A-tents and occasional wall tent on muddy flat ground, bundled firewood, field cooking smoke and parked supply wagon. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +5%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Scenario overlay: camps do not create permanent terrain changes or static supply automatically.

**1862 authenticity:** Military encampments and wagon parks accompanied campaigning armies; placements require a dated scenario record. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 33. Battlefield — `T_BATTLEFIELD`

**Category:** Military; **render layer:** `military`; **season:** Only after a battle in scenario timeline.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Trampled young wheat, broken fence rails, smoke wisps, scattered abandoned equipment and churned earth, no modern markers. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +5%; attack penalty -5%; movement 3 MP; production 0; VP Optional: battle objective.

**Special rules:** Only appears after a recorded engagement date; does not pre-exist in a March base map.

**1862 authenticity:** Combat debris reflects specific battles, but must be triggered after action, not painted into a pre-battle 1862 landscape. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 34. Hospital — `T_HOSPITAL`

**Category:** Military; **render layer:** `military`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Existing 1862-period house, school or public building temporarily used for casualties; stretchers and wagon nearby, no unverified yellow flag. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty 0%; movement 2 MP; production 0; VP Optional: hospital/supply.

**Special rules:** Medical function depends on dated scenario event; no native heal bonus assumed.

**1862 authenticity:** Civil War field hospitals used existing buildings; identification must match named/date-specific records. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 35. Headquarters — `T_HQ`

**Category:** Military; **render layer:** `military`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Existing plantation house, schoolhouse or tavern with tethered horses, plain courier saddle and minimal period staff evidence. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +15%; attack penalty 0%; movement 2 MP; production 0; VP Optional: headquarters.

**Special rules:** HQ command-radius and courier systems require separate Unity/Harmony implementation; no omniscient buff by tile alone.

**1862 authenticity:** Commanders used civilian buildings and tents as temporary headquarters during 1862 operations; use dated evidence. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 36. Muddy Road — `O_MUD`

**Category:** Seasonal overlay; **render layer:** `season`; **season:** March / after heavy spring rain.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Same existing wagon road with water-filled deep ruts, wet wheel tracks and brown roadside runoff after cold rain. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** Weather overlay on dirt road; artillery blocked only in severe saturation (Harmony/path rules).

**1862 authenticity:** Spring rains often made unimproved roads difficult in 1862; conditions varied by day. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 37. Flooded Ford — `O_FLOOD`

**Category:** Seasonal overlay; **render layer:** `season`; **season:** March–May after high water.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Verified ford with bank-to-bank chocolate water, submerged stones and a high-water mark on riparian trunks. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement BLOCK MP; production 0; VP No.

**Special rules:** Weather overlay switches approved ford to river-blocked mode; never creates a bridge.

**1862 authenticity:** Floods made many nineteenth-century Shenandoah fords hazardous or impassable after heavy rain. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 38. Burned Bridge — `O_BURNED_BRIDGE`

**Category:** Seasonal/damage overlay; **render layer:** `season`; **season:** Only after documented destruction event.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Broken timber abutments, charred planks and twisted bracing hanging above swift muddy water, ashes and little smoke after fire. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement BLOCK MP; production 0; VP Optional: destroyed crossing.

**Special rules:** Destroyed-state overlay on a historically attested bridge only after its destruction event; block movement.

**1862 authenticity:** Military parties destroyed bridges during the campaign, but each case must be dated and identified. **Placement status:** SOURCE-REQUIRED: feature location and 1862 date.



### 39. Winter Wheat — `O_WINTER_WHEAT`

**Category:** Seasonal field variant; **render layer:** `season`; **season:** March–May.

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Fine low bright-green wheat blades between brown early-spring furrows; slightly fuller in April but not a modern tall crop. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +0%; attack penalty 0%; movement 2 MP; production 0; VP No.

**Special rules:** Visual variant of Open Wheat Field, not an additional income-producing terrain class.

**1862 authenticity:** Overwintered wheat provided early green growth in cultivated Valley fields. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



### 40. Spring Orchard — `O_ORCHARD_BLOOM`

**Category:** Seasonal orchard variant; **render layer:** `season`; **season:** Late April–May (weather-dependent).

**Visual:** Flat-top hex, horizontal upper/lower edges and left/right points. Steep 75–80° high-oblique view looking north; soft northwest light and southeast shadow; roof planes dominate with only a slim south-facing wall visible; tree crowns dominate trunks. Orchard stems with restrained white-pink blossoms beginning on surviving apple/peach trees, straw grass still visible underneath. March: wet umber, straw ochre, ash gray and almost bare branches; April: translucent buds, pale wheat green and damp soil; May: modest leaf-out and richer wheat greens, still avoiding midsummer lushness.

**Hex of Steel balance proposal:** Defense +10%; attack penalty -5%; movement 3 MP; production 0; VP No.

**Special rules:** Late April/May date/weather-dependent skin of Orchard; retain same grid/tree masks and pathfinding.

**1862 authenticity:** Seasonal flowering of existing Valley orchards; exact bloom timing depends on altitude and year. **Placement status:** GENERAL PERIOD TYPE; exact placement source-required.



## References and provenance



- **Primary period cartography:** Jedediah Hotchkiss, *[Map of the Shenandoah Valley]*, 1862, Library of Congress, https://www.loc.gov/resource/g3882s.cwh00089/ . Drawn in 1862, but do not assume all battlefield changes predate its completion.

- **Campaign surveying context:** National Park Service, *Jedediah Hotchkiss’ Maps of the Shenandoah Valley*, https://www.nps.gov/articles/000/jedediah-hotchkiss-maps-of-the-shenandoah-valley.htm .

- **Engine rules:** *Hex of Steel Official Manual*, Steam-hosted PDF https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/1240630/manuals/a629ccb39360b1023aa0d2b2921e98e1c6b311de/Manual.pdf .

- **October 2023 update qualification:** the October 11, 2023 update includes economy and several gameplay changes, but this research did not verify that it introduced a new independent editable attack-penalty field. See https://steamdb.info/patchnotes/12414837/ .

- **Research use only:** The postwar Hotchkiss campaign plates issued in 1880 illustrate the battles but are not independent proof of the preexisting March 1862 building inventory.



## Native integration acceptance tests



1. Read a true tile from installed game via editor and confirm its `Name`, seasonal sprite resolution, `Type`, `FilterType`, movement and damage modifier semantics.

2. Compare native `Plain`, `Road`, `Forest`, `River`, `Bridge`, `Railroad`, `Village` behavior with proposed rows; map fields with versioned C# adapter and Harmony only where needed.

3. Validate every reciprocal edge-port mask against real PNG artwork. Never invent a native sprite filename; verify all composite crossings.

4. Create a tiny 5×5 playable sample; test March and May variant changes, infantry/cavalry/artillery/engineer movement, train continuity, bridge destruction, LOS, AI, save/load.

5. Confirm written `.sav` round trip in installed game before promoting catalog records from **proposed** to **native verified**.