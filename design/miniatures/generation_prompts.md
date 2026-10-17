# Generation record

Built-in `image_gen`, transparent background. User reference 1 (miniature stands)
was supplied as a style reference. Reference 2 was inspected for the desired
illustrated-counter treatment; its generated faces, baked statistics and banners
were not reused. Original uploaded reference images are not redistributed here.

## Shared stand prompt

Use case: historical-scene. Asset type: transparent PNG game unit sprite, painted 28mm tabletop miniatures on one low hexagonal flocked grass base, matching the first reference's miniature aesthetic, with superb sculpted cloth, muted natural pigments, tiny grass tufts and rocks. Three-quarter overhead view about 35 degrees down. Entire stand isolated with true transparent background; no terrain outside base. Center stand with 8 percent transparent margins. Base across lower half. Front edge has ONE empty dark round portrait medallion at front left, gold rim, wholly BLANK, no face or head inside; and a blank cream rectangular nameplate to its right, no text. All figure faces tiny indistinct tabletop paint marks, never a recognizable officer likeness or portrait. No counter frame, no numbers, no NATO icons, no text, no watermarks, no cast shadow outside base. Do not replicate inaccurate flags or the portrait faces from reference.

## Subjects and final constraints

- Garnett: Stonewall Brigade, March 23 1862; five advancing Virginia infantry,
  officer with sword and colour bearer; mixed gray/butternut, kepis/slouch hats,
  blanket rolls, rifle-muskets with bayonets; dark-blue Virginia state flag with
  a small seal; no battle cross. Generator supplied seven figures rather than
  five; figures are decorative and do not encode regimental strengths.
- Ashby: three mounted cavalry, leader on white horse, others brown/dark;
  mixed civilian/gray clothing, slouch hats, sabres/carbines; no flags or gun.
- Kimball: Union infantry, dark-blue sack coats, sky-blue trousers, forage caps
  and one Hardee hat; colonel with sword, no general stars. Initial 34-star flag
  request failed visual inspection. Final edit: remove the entire national flag,
  finial and pole; replace with transparent air and a vertically carried rifle;
  preserve figures, base, blank medallion, blank plate; no flags, portraits or text.
- Jackson: mounted on a small sorrel horse with pale mane; plain faded dark-blue
  professor-type coat and dark forage cap, no gold braid or gray general coat;
  one generic gray courier; no Hotchkiss, map holder, flag, pole or banner.
  Result includes a folded dispatch in the courier's hand; no named staff identity
  is assigned to that figure.

All names and actual portraits were added deterministically afterward by
`scripts/build_miniature_assets.py`. Native generation sizes were 1448x1086
(Garnett) and 1254x1254 (others), normalized to 2048 square working masters.
Upsampling is not additional native image detail.
