// DIY-Auto — debug: houdt brug A vast in één stand, zodat je rustig kunt meten. Start: ALLES UIT.
// Seriële monitor (115200): 'v' vooruit (HL+LR), 'a' achteruit (HR+LL), 'u' alles uit,
// '1' alleen HL, '2' alleen HR, '3' alleen LL, '4' alleen LR  (één transistor: nooit kortsluiting als de brug klopt).
// 'p' vooruit met PWM op LR (2 kHz, 70 %, zoals test_hbridge), 'q' idem op 200 Hz.
const int HL = 25, HR = 26, LL = 27, LR = 13;
bool pwmOn = false;
void pwmStop() { if (pwmOn) { ledcDetach(LR); pinMode(LR, OUTPUT); digitalWrite(LR, LOW); pwmOn = false; } }
void allesUit() { pwmStop(); digitalWrite(LL, LOW); digitalWrite(LR, LOW); digitalWrite(HL, LOW); digitalWrite(HR, LOW); delay(2); }
void zet(int a, int b, const char *t) { allesUit(); if (a >= 0) digitalWrite(a, HIGH); if (b >= 0) digitalWrite(b, HIGH); Serial.println(t); }
void setup() {
  for (int p : {HL, HR, LL, LR}) { digitalWrite(p, LOW); pinMode(p, OUTPUT); }
  Serial.begin(115200); delay(300);
  Serial.println("UIT (start)");
}
void loop() {
  if (!Serial.available()) return;
  char c = Serial.read();
  switch (c) {
    case 'v': zet(HL, LR, "VOORUIT: HL=1 LR=1 (rode led)"); break;
    case 'a': zet(HR, LL, "ACHTERUIT: HR=1 LL=1 (groene led)"); break;
    case 'u': zet(-1, -1, "UIT"); break;
    case '1': zet(HL, -1, "ALLEEN HL (linker IRF9540N)"); break;
    case '2': zet(HR, -1, "ALLEEN HR (rechter IRF9540N)"); break;
    case '3': zet(LL, -1, "ALLEEN LL (linker IRLZ44N)"); break;
    case '4': zet(LR, -1, "ALLEEN LR (rechter IRLZ44N)"); break;
    case 'p': case 'q': {
      int f = (c == 'p') ? 2000 : 200;
      zet(HL, -1, "");
      bool ok = ledcAttach(LR, f, 10); bool w = ledcWrite(LR, 716); pwmOn = true;
      Serial.printf("VOORUIT met PWM op LR: %d Hz, 70 %%  | attach=%d write=%d read=%lu\n", f, ok, w, (unsigned long)ledcRead(LR));
      break;
    }
  }
}
