// DIY-Auto — bankproef TB6612FNG-module: één motor tegelijk, zonder controller.
// Seriële monitor op 115200. Elke stap duurt 2 s:
//   A vooruit 30 % → A vooruit 70 % → A remmen → A achteruit 30 % → uit, daarna hetzelfde voor B.
// Labvoeding op 7,4 V met stroombegrenzing ±1 A. Gaat ze in CC, dan zit er een fout in de bedrading.

const int STBY = 18;
const int PIN[2][3] = {{25, 26, 27},   // A: IN1, IN2, PWM
                       {32, 33, 4}};   // B
const int PWM_FREQ = 20000, PWM_BITS = 10, PWM_MAX = (1 << PWM_BITS) - 1;

void pwmAttach(int pin, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, PWM_FREQ, PWM_BITS);
#else
  ledcSetup(ch, PWM_FREQ, PWM_BITS); ledcAttachPin(pin, ch);
#endif
}
void pwmWrite(int pin, int ch, uint32_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(ch, duty);
#endif
}

// m = 0 (A) of 1 (B); in1, in2 = richting; pct = 0..100
void step(int m, int in1, int in2, int pct, const char* what) {
  Serial.printf("motor %c: %s\n", 'A' + m, what);
  digitalWrite(PIN[m][0], in1);
  digitalWrite(PIN[m][1], in2);
  pwmWrite(PIN[m][2], m, (uint32_t)pct * PWM_MAX / 100);
  delay(2000);
}

void setup() {
  Serial.begin(115200);
  digitalWrite(STBY, LOW); pinMode(STBY, OUTPUT);
  for (int m = 0; m < 2; m++) {
    for (int i = 0; i < 2; i++) { digitalWrite(PIN[m][i], LOW); pinMode(PIN[m][i], OUTPUT); }
    pwmAttach(PIN[m][2], m);
    pwmWrite(PIN[m][2], m, 0);
  }
  digitalWrite(STBY, HIGH);
  Serial.println("test_tb6612 gestart");
}

void loop() {
  for (int m = 0; m < 2; m++) {
    step(m, 1, 0, 30, "vooruit 30 %");
    step(m, 1, 0, 70, "vooruit 70 %");
    step(m, 1, 1, 100, "remmen");
    step(m, 0, 1, 30, "achteruit 30 %");
    step(m, 0, 0, 0, "uit");
  }
}
