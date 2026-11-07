// DIY-Auto — pintest: zet GPIO25, 26, 27 en 13 elke seconde samen HOOG en dan LAAG.
// Meet met de draad LOS van het breadboard: pin ↔ GND van de ESP32 moet wisselen tussen 3,3 V en 0 V.
// De seriële monitor (115200) toont de stand én wat de pin zelf terugleest.
const int PINS[] = {25, 26, 27, 13};
void setup() {
  Serial.begin(115200);
  for (int p : PINS) pinMode(p, OUTPUT);
}
void loop() {
  static bool hoog = false;
  hoog = !hoog;
  for (int p : PINS) digitalWrite(p, hoog);
  delay(5);
  Serial.printf("%s  |  terug gelezen: 25=%d 26=%d 27=%d 13=%d\n", hoog ? "HOOG (3,3 V)" : "LAAG (0 V)   ",
                digitalRead(25), digitalRead(26), digitalRead(27), digitalRead(13));
  delay(995);
}
