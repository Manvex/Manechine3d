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

Aparatele din setul 02, plus `glute_ham_developer` și `hyperextension_45`, sunt reconstruite cu `tools/upgrade_machines.py`:

- profile de cadru cu colțuri rotunjite, ceva mai groase, cu capace de plastic; cadru gri-argintiu
- perne tapițate bombate, role cu capete rotunjite, manșoane de prindere cu guler
- greutăți cu etichete și cui selector, carcasă pe turnul de greutăți, plăcuță de instrucțiuni
- tijă de șezut cromată cu buton galben de reglaj, capace pe axele pivoților

Nodurile `anchor_*` și `joint_*` (nume, poziții, `extras`) sunt identice cu cele din modelul original.
Modelele originale sunt în `glb_src/`; de acolo pornește scriptul:

```bash
python3 tools/upgrade_machines.py machine_chest_press --render
```

Materiale noi în GLB: `shroud`, `label`, `accent`. Gabaritul crește cu câțiva milimetri din cauza profilelor mai groase.
