# Referințe pentru echipamente

Am folosit doar dimensiuni publice. Modelele sunt generice, fără forme sau logo-uri de produs.
Valorile marcate „estimat” în `assets/equipment/manifest.json` nu au o sursă directă și trebuie verificate.

| Piesă | Valori folosite | Surse |
|---|---|---|
| Bară olimpică | 2200 mm, 20 kg, Ø28 mm, manșon Ø50 mm, 415 mm încărcabil | [Torokhtiy](https://torokhtiy.com/blogs/guides/olympic-barbell-dimensions), [Strength Shop](https://strengthshop.eu/products/riot-weightlifting-bar-men-s-20kg-iwf-specification) |
| Bară EZ | 1200 mm, Ø28 mm, manșon ~175 mm | [Gym Equipment UK](https://gymequipment.co.uk/pro-olympic-ez-curl-bar), [Fitness Superstore](https://fitnesssuperstore.com/products/french-fitness-black-47-olympic-ez-curl-bar-new) |
| Discuri bumper | Ø450 mm; 34 / 47 / 60 / 73 mm pentru 10 / 15 / 20 / 25 kg | [Garage Gym Reviews](https://www.garagegymreviews.com/?p=59290), [Decathlon](https://www.decathlon.ch/en/p/mp/competition-bumper-plate/20b13005-c16b-4c84-b35b-f07e079a9be3/c5) |
| Ganteră hex | 10 kg: 310 × 135 × 117 mm, mâner 130 mm, Ø31 mm; restul scalate după masă | [Gymsportz](https://gymsportz.sg/products/pivot-tpu-hex-dumbbells-set-d-8kg-to-30kg), [Aosom](https://aosom.co.uk/item/homcom-hex-dumbbell-rubber-weights-sets-hexagonal-gym-fitness-lifting-home-a91-019v01~A91-019V01.html) |
| Kettlebell | 282 × 208 mm, bază Ø140 mm, mâner Ø33 mm | [Rogue](https://www.roguefitness.com/eu/rogue-competition-kettlebells) |
| Bancă plată | 1200 × 749 × 426 mm, perne ~60 mm | [Impulse IPF](https://www.littleblokefitness.com.au/products/impulse-flat-bench-press), [Gym Gear](https://gymgear.com/cdn/shop/files/Sterling_Series_Flat_Bench.pdf) |
| Bancă reglabilă | spate 915 × 280 × 57 mm, șezut 380 mm, −10°…+85°, 650 × 1330 mm | [Titan](https://titan.fitness/products/scratch-and-dent-elite-series-adjustable-fid-bench-navy), [Jordan](https://www.gymequipment.co.uk/jordan-adjustable-fid-bench) |
| Rack | montanți 75 × 75 mm, găuri la 50 mm, H ~2300 mm, ~1450 × 1250 mm | [Factory Weights](https://factoryweights.co.uk/products/power-rack-long-with-storage), [Kings Gym](https://www.kingsgym.it/en/racks-75x75x3/567-half-rack-pro-75x75x3.html) |

Orificiile montanților sunt modelate la Ø22 mm, în intervalul listat de producători (17–26 mm).
Cele două direcții de găuri sunt decalate cu 25 mm, ca să rămână curată operația booleană.

## Convenții de model

- Unități: metri. În GLB, axa Y este în sus.
- Echipamentele fixe au originea pe podea. Obiectele ținute în mână au originea în centrul mânerului sau al barei.
- Nodurile `anchor_*` marchează punctele de contact pentru IK: mâini, șezut, sprijin bară.

## Aparate (setul 02)

Pentru aparate dimensiunile diferă mult între producători, așa că verificarea folosește intervale, nu o singură valoare.

| Piesă | Interval sau valori folosite | Surse |
|---|---|---|
| Functional trainer | 1620–1850 × 810–1090 × 2120–2260 mm | [Body-Solid GDCC210](https://www.ironcompany.com/cable-machine-gym-gdcc210), [Delta Fitness](https://www.delta-fitness.com/ar-sa/products/functional-trainer-with-dual-90-kg-weight-stacks), [Taurus](https://www.fitshop.nl/en/taurus-dual-pulley-functional-trainer-tf-cf820_95) |
| Smith | 1300–1320 × 2130–2250 × 2180–2290 mm, cursă 7°, 1540 mm, bară Ø35 mm | [Precor VBR6802](https://assets.precor.com/en-US/products/VBR6802), [Precor DPL0802](https://www.precor.com/en-US/products/DPL0802), [Hoist CF-3755](https://www.thefitnessoutlet.com/hoist-cf-3755-commercial-dual-action-smith-machine) |
| Leg press 45° | 2200–2800 × 1360–1880 × 1370–1580 mm, placă 750 × 600, spătar 900 × 400 mm | [BLK BOX](https://www.blkboxfitness.com/products/blk-box-45-degree-plate-loaded-leg-press-machine), [Perform Better](https://www.performbetter.com/Signature-Series-Plate-Loaded-45-Leg-Press/), [YR Fitness](https://www.yanrefitness.com/product/7329-45-leg-press) |
| Lat pulldown / ramat | 1750–2000 × 1200–1320 × 2210–2390 mm | [Bodykore GR638](https://media.bodykore.com/pdfs/GR638.pdf), [Precor Vitality](https://www.beyondthebasicsfitness.com/product/precor-vitality-pulldown-seated-row/), [Spirit](https://thefitnessoutlet.com/products/spirit-fitness-lat-pulldown-row) |
| GHD | 1520–2210 × 720–800 × 1130–1170 mm | [Sideaita](https://www.sideaita.it/en/?p=902), [French Fitness](https://fitnesssuperstore.com/French-Fitness-GHD-Compact-Roman-Chair-GHD30-New-p/ff-ghd30.htm) |
| Tracțiuni asistate | 1065–1475 × 1295–1830 × 2110–2290 mm | [RPM Power](https://rpmpower.com/?p=296079), [Titan](https://titan.fitness/products/plate-loaded-assisted-pull-up-and-dip-machine-1), [Body-Solid](https://bodysolid.com/body-solid-pro-select-weight-assist-chin-up-dip) |

Celelalte aparate au gabarit estimat, marcat în `manifest.json`, și nu trec printr-o verificare dimensională.

Banda de alergare (`treadmill_flat`, `treadmill_incline`), turnul cu scripete (`cable_tower_high`), bara V și gantera rotundă sunt modelate după conturul din clipurile de referință, cu `tools/clip_plane.py`, deci proporțiile lor vin din clip, nu din fișe de produs.

## Piese mobile

- Nodurile `joint_*` sunt pivoții pieselor mobile. În `extras` au `kind`, `axis_gltf` și `limits`.
- `kind` este `rotary` (grade), `linear` (metri) sau `ball` (rotație liberă în jurul pivotului, pentru landmine).
- Valoarea 0 este poziția de repaus din GLB.
- Cablurile nu sunt modelate: viewerul le desenează între ancorele `cable_*` și accesoriu.

## Aspect realist (aparate)

Cele 28 de aparate din setul 02 (plus `glute_ham_developer` și `hyperextension_45`) sunt reconstruite cu `tools/upgrade_machines.py`.
Fiecare are o rețetă de cadru scrisă de mână în `tools/machine_recipes.py`, făcută după poze de produs ale unor aparate comerciale.
Modelele rămân generice, fără forme sau logo-uri de produs.

- cadru din țevi îndoite continue (nu bare sudate cap la cap), cu picioare de cauciuc și lagăre la pivoți
- turn de greutăți carcasat: două coloane, panou spate, panou frontal sus cu plăcuță, capac, soclu
- perne tapițate bombate, role cu capete rotunjite, manșoane de prindere, came la pivoții pârghiilor
- tijă de șezut cromată și butoane galbene de reglaj; coarne de discuri la aparatele cu discuri

Nodurile `anchor_*` și `joint_*` (nume, poziții, `extras`) sunt identice cu cele din modelul original, păstrat în `glb_src/`.
Materiale noi în GLB: `shroud`, `label`, `accent`.

```bash
python3 tools/upgrade_machines.py machine_chest_press --render
```

`--dump` listează piesele modelului original, iar `--preview` face patru vederi rapide.

### Referințe vizuale pe aparat

| Aparat | Referințe |
|---|---|
| `machine_chest_press` | [BodyKore GR601](https://selectfitness.com/products/bodykore-chest-press-gr601), [Muscle D Classic V2](https://www.americanfitness.net/products/classic-v2-selectorized-chest-press), [Precor Vitality](https://pushpedalpull.com/products/commercial-precor-vitality%E2%84%A2-series-chest-press) |
| `machine_incline_press`, `plate_incline_press` | [Hammer Strength Iso-Lateral Incline Press](https://www.lifefitness.com/en-us/catalog/strength-training/plate-loaded/plate-loaded-iso-lateral-incline-press) |
| `machine_shoulder_press`, `plate_shoulder_press` | [Life Fitness Insignia Shoulder Press](https://www.lifefitness.com/en-us/catalog/strength-training/selectorized/insignia-series-shoulder-press), [Hammer Strength Iso-Lateral Shoulder Press](https://www.lifefitness.com/en-us/catalog/strength-training/plate-loaded/plate-loaded-iso-lateral-shoulder-press) |
| `plate_chest_press` | [Hammer Strength Iso-Lateral Bench Press](https://www.lifefitness.com/en-us/catalog/strength-training/plate-loaded/plate-loaded-iso-lateral-bench-press) |
| `machine_seated_row`, `plate_row` | [Hammer Strength Iso-Lateral Row](https://www.lifefitness.com/en-us/catalog/strength-training/plate-loaded/plate-loaded-iso-lateral-row) |
| `machine_pec_deck` | [Skelcore Power Series](https://www.skelcore.com/products/power-series-rear-delt-pec-fly-pin-load), [Muscle D Classic V2](https://www.americanfitness.net/products/classic-v2-selectorized-pec-rear-delt-combo), [Gronk](https://livefit.com/products/gronk-fitness-selectorized-pec-fly-rear-delt) |
| `machine_leg_extension`, `machine_leg_curl_seated` | [Life Fitness Axiom](https://shop.lifefitness.com/products/axiom-series-seated-leg-curl-extension), [Skelcore Power Series](https://www.skelcore.com/products/power-series-leg-curl-extension-pin-load), [SFE](https://omahasportsandgames.com/products/sfe-selectorized-seated-leg-extension-leg-curl-machine-250lb-weight-stack) |
| `machine_leg_curl_lying` | [Skelcore Prone Leg Curl](https://www.skelcore.com/products/power-series-prone-leg-curl-pin-load), [Muscle D Classic V2](https://www.americanfitness.net/products/classic-v2-selectorized-prone-leg-curl) |
| `machine_hip_abduction_adduction` | [SFE Hip Abductor/Adductor](https://omahasportsandgames.com/products/sfe-selectorized-hip-abductor-adductor-machine-250lb-weight-stack) |
| `machine_preacher_curl`, `machine_triceps_extension` | [Life Fitness Axiom Biceps/Triceps](https://shop.lifefitness.com/products/axiom-series-biceps-curl-triceps-extension), [elitefts Preacher Curl](https://elitefts.com/products/elitefts-preacher-curl-selectorized) |
| `machine_ab_crunch` | [Hammer Strength Select Abdominal Crunch](https://shop.lifefitness.com/products/hammer-strength-select-abdominal-crunch) |
| `machine_rotary_torso` | [Technogym Selection Rotary Torso](https://fitnesssuperstore.com/Technogym-Selection-Rotary-Torso-Rotation-p/tgselrotr.htm), [Muscle D Elite MDE-18](https://www.ironcompany.com/muscle-d-fitness-rotary-torso-mde-18) — doar descrieri, pozele nu s-au încărcat |
| `machine_calf_standing` | [Skelcore Standing Calf](https://www.skelcore.com/products/power-series-standing-calf-pin-load), [Muscle D Classic V2](https://www.americanfitness.net/products/classic-v2-selectorized-standing-calf-raise) |
| `machine_assisted_pullup_dip` | [Skelcore Dip/Chin Assist](https://www.skelcore.com/products/power-series-dip-chin-assist-pin-load) |
| `cable_crossover` | [Skelcore Cable Crossover](https://www.skelcore.com/products/cable-crossover), [Body-Solid Series II](https://www.americanfitness.net/products/series2-cable-crossover) |
| `cable_functional_trainer` | [Precor Resolute Dual Adjustable Pulley](https://pushpedalpull.com/products/commercial-precor-resolute%E2%84%A2-dual-adjustable-pulley), [Northern Fitness DAP](https://www.northernfitness.ca/products/commercial-dual-adjustable-pulley-functional-trainer) |
| `cable_lat_row_combo` | [elitefts Lat Pulldown w/ Low Row](https://elitefts.com/products/elitefts-lat-pulldown-machine-with-low-row-selectorized) |
| `smith_machine` | [Northern Fitness](https://www.northernfitness.ca/products/commercial-dual-adjustable-pulley-functional-trainer) (cadru Smith combinat) plus dimensiunile din tabelul de mai sus |
| `hack_squat` | [Extreme Training Equipment](https://extremetrainingequipment.com/products/hack-squat-1), [Titan](https://titan.fitness/products/plate-loaded-linear-hack-squat-machine) |
| `leg_press_45` | [BLK BOX 45°](https://www.blkboxfitness.com/en-us/products/blk-box-45-degree-plate-loaded-leg-press-machine) |
| `plate_calf_seated` | [Skelcore Seated Calf Raise](https://www.skelcore.com/products/seated-calf-raise), [Gym Gear Pro Series](https://gymgear.com/products/pro-series-plate-loaded-seated-calf-raise) |
| `glute_ham_developer` | [French Fitness GHD20](https://fitnesssuperstore.com/French-Fitness-GHD-Glute-Ham-Developer-Roman-Chair-New-p/ff-ghd20.htm) |
| `hyperextension_45` | [CAP 45° Hyperextension](https://www.garagegymreviews.com/equipment/cap-strength-45-degree-hyperextension) — doar descriere, poza nu s-a încărcat |
