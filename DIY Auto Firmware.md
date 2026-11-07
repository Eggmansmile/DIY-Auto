#electronics #project #firmware

*[[DIY Auto]] · [[DIY Auto Elektronica|Elektronica]] · [[DIY Auto Breadboard|Breadboard]] · [[DIY Auto Firmware|Firmware]] · [[DIY Auto Mechanisch|Mechanisch]] · [[DIY Auto BOM|BOM]] · [[Taken DIY-Auto|Taken]]*

## Eerst: H-brug testen zonder controller

Sketch: `Firmware/test_hbridge/test_hbridge.ino`. Gewoon Espressif-bordpakket (`esp32`), bord *ESP32 Dev Module*, seriële monitor op 115200. De lus: 2 s vooruit 70 % (rode led), uit, 2 s achteruit (groene led), uit, dan vooruit met PWM van 0 naar 70 % (de led wordt feller). Kijk naar de labvoeding: een paar mA is goed, loopt de stroom naar 0,5 A, dan meteen de USB eruit.

Flashen kan ook zonder IDE, `arduino-cli` staat op de laptop:

```
arduino-cli core install esp32:esp32
arduino-cli compile --fqbn esp32:esp32:esp32 Firmware/test_hbridge
arduino-cli upload -p /dev/ttyUSB0 --fqbn esp32:esp32:esp32 Firmware/test_hbridge
arduino-cli monitor -p /dev/ttyUSB0 -c baudrate=115200
```

## Daarna: rijden met de Xbox-controller

Sketch: `Firmware/test_drive/test_drive.ino`. Linkerjoystick = gas (beide motoren), rechterjoystick = sturen, B = remmen. Controller weg = motoren uit.

Arduino IDE instellen (één keer):

1. **Voorkeuren → Extra URL's voor bordenbeheer**, beide regels toevoegen:
   `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
   `https://raw.githubusercontent.com/ricardoquesada/esp32-arduino-lib-builder/master/bluepad32_files/package_esp32_bluepad32_index.json`
2. **Bordenbeheer:** installeer `esp32` (Espressif) en `esp32_bluepad32`.
3. **Bord:** Tools → Board → ESP32 + Bluepad32 Arduino → *ESP32 Dev Module*. Poort = de CH340.
4. Uploaden, seriële monitor op 115200.
5. **Xbox-controller koppelen:** Xbox-knop aan, dan de kleine koppelknop bovenaan ingedrukt houden tot het logo snel knippert. In de monitor verschijnt "controller verbonden". Werkt het niet: de controller-firmware bijwerken via de Xbox Accessories-app (Bluetooth LE nodig).

Instellingen bovenaan in de sketch:

| Constante | Standaard | Waarom |
|---|---|---|
| `MAX_PWM` | 0,70 | 3–6 V-motoren op 7,4 V |
| `MOTOR_B_INVERT` | true | motor B zit gespiegeld; draait een wiel verkeerd, omdraaien |
| `USE_VBAT_CUTOFF` | false | op het breadboard zitten R41/R42 niet; op de print op `true` zetten (stop onder 6,4 V) |
| `SERVO_RANGE` | ±145 µs | hoorn ±17,5° → binnenwiel 30°, buitenwiel 26° (hefboom 1,6×). Stuurt hij verkeerd om: `STEER_INVERT = true` |

Testen: eerst met de testlast met leds (stap 5 van het breadboard). Joystick naar voren: rode led; naar achteren: groene led; half: dimmer.
