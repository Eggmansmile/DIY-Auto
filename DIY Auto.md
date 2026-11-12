#3d-printen #elektronica #project

Referentieblad voor de RC-auto. Alles wat je tijdens het designen moet kunnen opzoeken.

- **CAD:** `CAD/DIY-Auto.sc` (SolidCraft, met joints) · [Onshape projectfolder](https://cad.onshape.com/documents?nodeId=4bc9426927f8be523bc07b16&resourceType=folder)
- **Taken:** [[Taken DIY-Auto]]
- **Onderdelen:** [[DIY Auto BOM]]

## Doelen

1. KiCad leren en een eigen PCB maken met de ESP32 erop.
2. Een designworkflow opbouwen: per deelsysteem tekenen, printen, testen.
3. Rijden en sturen met een Xbox-controller.

## Deelnotes

| Note | Wat erin staat |
|---|---|
| [[DIY Auto Elektronica]] | schema, H-brug, voeding en eerste keer aanzetten, pinout en stuurtabel, KiCad-scripts |
| [[DIY Auto Breadboard]] | de 9 bouwstappen van het breadboard (Fritzing) |
| [[DIY Auto Firmware]] | H-brug-test zonder controller, rijden met de Xbox-controller, instellingen |
| [[DIY Auto Mechanisch]] | 3D-model, printdelen, sturing, SolidCraft-assembly, maten in `params.py` |
| [[Testblok passingen]] | het testblokje: wat waar in moet, wat je terugmeldt |
| [[PCB bestellen en solderen]] | PCBWay-bestelling, wat je nog koopt, soldeervolgorde |
| [[DIY Auto Assemblage]] | monteren na het printen, met een beeld per stap |
| [[DIY Auto BOM]] · [[Taken DIY-Auto]] | onderdelen en wat nog moet |

![[DIYAuto_sturing_iso.gif|380]] ![[DIYAuto_aandrijving_9to1.gif|320]]

## Links

- [Bluepad32](https://github.com/ricardoquesada/bluepad32)
- [kicad-sch-api](https://pypi.org/project/kicad-sch-api/): de Python-library achter het script
- [SRA-board](https://github.com/SRA-VJTI/sra-board-hardware-design): open ESP32-robotbord in KiCad, ter vergelijking
- [[PCB's (Printed Circuit Board)]] · [[Threaded Inserts 3D Printing]] · [[Microcontrollers]] · [[Testblok passingen]]
- **Ontwerpkennis:** [[Threaded Inserts 3D Printing]] · [[Vrijheidsgraden en verbindingen]] · [[Tandwielen ontwerpen]] · [[Motoren en servo's koppelen]] · [[Lagers]] · [[Passingen en toleranties]] · [[Printrichting en sterkte]] · [[H-Brug]] · [[DC-motor karakteristiek]]
