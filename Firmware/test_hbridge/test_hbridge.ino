// DIY-Auto — eerste test van H-brug A zonder controller.
// Board: gewone "ESP32 Dev Module" (Espressif esp32-pakket), geen Bluepad32 nodig.
// Doet in een lus: 2 s vooruit (rode led), 1 s uit, 2 s achteruit (groene led), 1 s uit, en dan hetzelfde
// met PWM van 0 naar 70 % (de led wordt geleidelijk feller). Seriële monitor op 115200 toont wat er gebeurt.
// Regel: HL en LL nooit samen aan, HR en LR ook niet (kortsluiting). Tussen twee richtingen altijd alles uit.

const int HL = 25, HR = 26, LL = 27, LR = 13;   // brug A, zoals in het schema
const int PWM_FREQ = 2000, PWM_BITS = 10, PWM_MAX = (1 << PWM_BITS) - 1;
const float MAX_PWM = 0.70;

void pwmAttach(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, PWM_FREQ, PWM_BITS);
#else
  ledcSetup(ch, PWM_FREQ, PWM_BITS); ledcAttachPin(pin, ch);
#endif
}
void pwm(int pin, int ch, float duty) {          // duty 0..1
  uint32_t d = (uint32_t)(duty * PWM_MAX);
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, d);
#else
  ledcWrite(ch, d);
#endif
}

void allesUit() {
  pwm(LL, 0, 0); pwm(LR, 1, 0);
  digitalWrite(HL, LOW); digitalWrite(HR, LOW);
  delay(2);                                      // dode tijd
}
void vooruit(float duty)   { allesUit(); digitalWrite(HL, HIGH); pwm(LR, 1, duty); }   // HL + LR
void achteruit(float duty) { allesUit(); digitalWrite(HR, HIGH); pwm(LL, 0, duty); }   // HR + LL

void setup() {
  digitalWrite(HL, LOW); pinMode(HL, OUTPUT);
  digitalWrite(HR, LOW); pinMode(HR, OUTPUT);
  pwmAttach(LL, 0); pwmAttach(LR, 1);
  allesUit();
  Serial.begin(115200);
  Serial.println("test_hbridge: brug A");
}

void loop() {
  Serial.println("vooruit 70 %  -> rode led");   vooruit(MAX_PWM);   delay(2000);
  Serial.println("uit");                          allesUit();         delay(1000);
  Serial.println("achteruit 70 % -> groene led"); achteruit(MAX_PWM); delay(2000);
  Serial.println("uit");                          allesUit();         delay(1000);
  Serial.println("vooruit, PWM 0 -> 70 %");
  for (int i = 0; i <= 70; i += 5) { vooruit(i / 100.0); Serial.printf("  %d %%\n", i); delay(300); }
  allesUit(); delay(1000);
}
