# DIY-Auto — BOM uit het CAD-model

Gegenereerd door `Scripts/cad/export_sc.py`. Aankoopstatus en links: [[DIY Auto BOM]].

## Geprint

| # | Onderdeel | Materiaal / spec | Subassembly |
|---|---|---|---|
| 1 | body | ASA black, one piece (v5: chassis + nose merged), floor on the bed | 1 frame |
| 1 | clamp_L | ASA black, split face on the bed | 1 frame |
| 1 | clamp_R | ASA black, split face on the bed | 1 frame |
| 1 | rim_rear_L | PLA (ASA later), 0.2 nozzle (m0.5 teeth) | 2 rear drive |
| 1 | tyre_rear_L | TPU 90A | 2 rear drive |
| 1 | rim_rear_R | PLA (ASA later), 0.2 nozzle (m0.5 teeth) | 2 rear drive |
| 1 | tyre_rear_R | TPU 90A | 2 rear drive |
| 1 | rim_front_L | PLA (ASA later) | 3 front wheels |
| 1 | tyre_front_L | TPU 90A | 3 front wheels |
| 1 | rim_front_R | PLA (ASA later) | 3 front wheels |
| 1 | tyre_front_R | TPU 90A | 3 front wheels |
| 1 | knuckle_L | ASA black, stands on its flat feet (inner side down), spacer up | 4 steering |
| 1 | knuckle_R | ASA black, stands on its flat feet (inner side down), spacer up | 4 steering |
| 2 | servo_clamp | ASA black, 2 flat bars 4.5 mm over the servo tabs (one STL holds both) | 4 steering |
| 1 | servo_horn | ASA black, printed horn 4 mm: press onto the 4.76 spline (bore 4.78) (drop of CA if loose); the tie rods on the pin keep it down; top face on the bed | 4 steering |
| 1 | tie_rod_L | ASA black, 3.5 x 7 flat, top on the bed; pivots on M4 + 2 jammed nuts, must turn freely | 4 steering |
| 1 | tie_rod_R | ASA black, 3.5 x 7 flat, top on the bed; pivots on M4 + 2 jammed nuts, must turn freely | 4 steering |
| 2 | spacer_buck | ASA black spacer Ø6 x 3, M3 hole: between LM2596 and PCB (plastic, a metal nut would touch IN+) | 5 electronics |

## Gekocht

| # | Onderdeel | Materiaal / spec | Subassembly |
|---|---|---|---|
| 4 | bearing_MR105_rear | MR105-2RS 5x10x4 | 2 rear drive |
| 2 | shim_rear | Shim washer 5x7x0.5 stainless (inner race only) | 2 rear drive |
| 4 | bearing_MR105_front | MR105-2RS 5x10x4 | 3 front wheels |
| 2 | shim_front | Shim washer 5x7x0.5 stainless (inner race only) | 4 steering |
| 1 | servo | SpringRC SM-S2309S (have), upright, body through the floor, tabs held down by the 2 printed clamp bars | 4 steering |
| 1 | buck_LM2596 | LM2596 module 43x21 on the PCB (J6/J7): trimpot to 5.0 V first, then 2x M3x10 + nut, pads soldered with wire stubs | 5 electronics |
| 1 | battery_2S | ERYNK 7.4 V 1500 mAh 2S pack (80x41x18.72 measured), JST BEC, in a 3 mm floor pocket + elastic band | 5 electronics |
| 1 | devkit_ESP32 | ESP32 DevKit v1 30-pin (Heemol, have) | 5 electronics |

## Bevestiging

| # | Onderdeel | Materiaal / spec | Subassembly |
|---|---|---|---|
| 8 | insert_M3x6_strap | HEAT-SET INSERT M3x6: body, top of the 8 motor-saddle ears (press in with the soldering iron before the motor goes in) | 1 frame |
| 8 | screw_M3x10_strap | BOLT M3x10 socket head: through the motor strap clamp into the ear insert | 1 frame |
| 4 | insert_M3x6_pcb | HEAT-SET INSERT M3x6: body, top of the 4 PCB standoffs | 1 frame |
| 2 | axle_bolt_M5x40 | BOLT M5x40 socket head: rear axle, from the wheel side (M5x30 is too short for the nylock) | 2 rear drive |
| 2 | nut_M5_rear | PLAIN NUT M5 (no insert): dropped into the slot in the axle tower from the top, tighten fully (clamps the inner races, the bolt does not turn) | 2 rear drive |
| 2 | axle_bolt_M5x20 | BOLT M5x20 socket head: front axle from the wheel side, threadlocker | 4 steering |
| 2 | nut_M5_front | PLAIN NUT M5 (no insert): in the hex pocket on the inside of the knuckle, before the knuckle goes on | 4 steering |
| 4 | insert_M3x6_servo | HEAT-SET INSERT M3x6: body, top of the 2 servo towers (4x), before the servo goes in | 4 steering |
| 4 | screw_M3x10_servo | BOLT M3x10 socket head: through the servo clamp bars into the tower inserts | 4 steering |
| 3 | screw_M4_steering | BOLT M4x20 (horn pin) + M4x25 (left arm) + M4x30 (right arm): from below, head under the horn / arm boss | 4 steering |
| 6 | nut_M4_steering | 2 PLAIN NUTS M4 per pivot, on top of the tie rods: jam them (first snug, back off 1/8, lock the second); the rods must turn freely | 4 steering |
| 2 | kingpin_M4x30 | BOLT M4x30 socket head: kingpin, head down through both knuckle lugs and the beam | 4 steering |
| 4 | nut_M4_kingpin | 2 PLAIN NUTS M4 per kingpin, on top: first one until the play is gone, back off 1/8 turn, hold it and lock the second against it | 4 steering |
| 2 | screw_M3x10_buck | BOLT M3x10 socket head: LM2596 hole -> printed spacer -> PCB | 5 electronics |
| 2 | nut_M3_buck | NUT M3 (ISO 4032) under the PCB, 2.5 mm above the battery | 5 electronics |
| 4 | screw_M3x6_pcb | BOLT M3x6 socket head: through the PCB corner hole into the standoff insert (max M3x10) | 5 electronics |
