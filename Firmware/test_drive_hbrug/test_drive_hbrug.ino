// DIY-Auto — testfirmware voor het BREADBOARD met de eigen MOSFET-H-bruggen (rev 3). Op de print (rev 4, TB6612) gebruik je test_drive.
//
// Board: "ESP32 Dev Module" uit het Bluepad32-boardpakket (esp32_bluepad32), zie [[DIY Auto]] → Firmware.
// Pinnen volgen het KiCad-schema en de Fritzing-tekening (rev 3):
//   motor A (links):  HL 25, HR 26, LL 27 (PWM), LR 13 (PWM)
//   motor B (rechts): HL 32, HR 33, LL 4  (PWM), LR 18 (PWM)
//   servo 19, accumeting 34
//
// Besturing:
//   linkerjoystick Y  = gas (vooruit / achteruit), beide motoren
//   rechterjoystick X = sturen (servo)
//   B ingedrukt       = remmen (beide lage kanten aan)
//   controller weg     = motoren uit, servo in het midden
//
// Regels uit de note (stuurtabel):
//   - HL en LL nooit samen aan, HR en LR ook niet: dat is kortsluiting over de accu.
//   - Vooruit: HL = 1, LR = PWM.  Achteruit: HR = 1, LL = PWM.  Remmen: LL = LR = 1.
//   - Richting wisselen: alles uit, 1 ms wachten, dan pas de andere kant aan.

#include <Bluepad32.h>

// ------------------------------------------------------------------ instellingen
const float MAX_PWM        = 0.70;   // 3–6 V-motoren op 7,4 V: 70 % ≈ 5,2 V gemiddeld
const bool  MOTOR_B_INVERT = true;   // motor B zit gespiegeld; draait hij verkeerd om, zet dit op false
const bool  MOTOR_A_INVERT = false;
const int   DEADZONE       = 40;     // joystick -511..512
const bool  USE_VBAT_CUTOFF = false; // true zodra R41/R42 er zitten (op het breadboard niet: GPIO34 zweeft)
const float VBAT_MIN       = 6.4;    // V, 3,2 V per cel
const float VBAT_DIVIDER   = 25.1 / 5.1;   // R41 20k, R42 5k1

const int PWM_FREQ = 2000;           // Hz, 1–5 kHz: de motor zoemt, dat is normaal
const int PWM_BITS = 10;
const int PWM_MAX  = (1 << PWM_BITS) - 1;

const int SERVO_PIN   = 19;
const int SERVO_FREQ  = 50;
const int SERVO_BITS  = 14;
const int SERVO_MID   = 1500;        // µs
const int SERVO_RANGE = 145;         // ± µs ≈ ±17,5° hoorn (SM-S2309S: ±60° bij ±500 µs) → binnenwiel 30°, buitenwiel 27° (hefboom 1,6×)
const bool STEER_INVERT = false;     // stuurt de auto de verkeerde kant op? zet op true
const int VBAT_PIN    = 34;

// ------------------------------------------------------------------ PWM-hulp (arduino-esp32 2.x en 3.x)
void pwmAttach(int pin, int freq, int bits, int ch) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcAttach(pin, freq, bits);
#else
  ledcSetup(ch, freq, bits);
  ledcAttachPin(pin, ch);
#endif
}
void pwmWrite(int pin, int ch, uint32_t duty) {
#if ESP_ARDUINO_VERSION_MAJOR >= 3
  ledcWrite(pin, duty);
#else
  ledcWrite(ch, duty);
#endif
}

// ------------------------------------------------------------------ H-brug
struct Motor {
  const char* name;
  int hl, hr, ll, lr;      // pinnen
  int chLL, chLR;          // LEDC-kanalen (alleen arduino-esp32 2.x)
  bool invert;
  int dir;                 // -1 achteruit, 0 uit, +1 vooruit, 2 remmen
  uint32_t offSince;       // millis() waarop alles uit ging
};

Motor motA = {"A", 25, 26, 27, 13, 0, 1, MOTOR_A_INVERT, 0, 0};
Motor motB = {"B", 32, 33, 4, 18, 2, 3, MOTOR_B_INVERT, 0, 0};

// eigen prototypes: anders zet Arduino ze boven struct Motor en compileert het niet
void allOff(Motor& m);
void motorInit(Motor& m);
void motorSet(Motor& m, float speed, bool brake);

void allOff(Motor& m) {
  pwmWrite(m.ll, m.chLL, 0);
  pwmWrite(m.lr, m.chLR, 0);
  digitalWrite(m.hl, LOW);
  digitalWrite(m.hr, LOW);
  if (m.dir != 0) m.offSince = millis();
  m.dir = 0;
}

void motorInit(Motor& m) {
  digitalWrite(m.hl, LOW); pinMode(m.hl, OUTPUT);
  digitalWrite(m.hr, LOW); pinMode(m.hr, OUTPUT);
  pwmAttach(m.ll, PWM_FREQ, PWM_BITS, m.chLL);
  pwmAttach(m.lr, PWM_FREQ, PWM_BITS, m.chLR);
  m.dir = 1;               // zodat allOff de tijd zet
  allOff(m);
}

// speed -1..+1; brake = beide lage kanten aan
void motorSet(Motor& m, float speed, bool brake) {
  if (m.invert) speed = -speed;
  int want = brake ? 2 : (speed > 0.01 ? 1 : (speed < -0.01 ? -1 : 0));

  if (want != m.dir) {                       // andere toestand: eerst alles uit, 1 ms dode tijd
    if (m.dir != 0) allOff(m);
    if (want == 0 || millis() - m.offSince < 2) return;   // 2 ticks ≥ 1 ms
  }

  uint32_t duty = (uint32_t)(fabsf(speed) * MAX_PWM * PWM_MAX);
  switch (want) {
    case 1:                                  // vooruit: HL aan, LR PWM (HR en LL blijven uit)
      digitalWrite(m.hr, LOW); pwmWrite(m.ll, m.chLL, 0);
      digitalWrite(m.hl, HIGH); pwmWrite(m.lr, m.chLR, duty);
      break;
    case -1:                                 // achteruit: HR aan, LL PWM
      digitalWrite(m.hl, LOW); pwmWrite(m.lr, m.chLR, 0);
      digitalWrite(m.hr, HIGH); pwmWrite(m.ll, m.chLL, duty);
      break;
    case 2:                                  // remmen: hoge kanten uit, beide lage kanten aan
      digitalWrite(m.hl, LOW); digitalWrite(m.hr, LOW);
      pwmWrite(m.ll, m.chLL, PWM_MAX); pwmWrite(m.lr, m.chLR, PWM_MAX);
      break;
  }
  m.dir = want;
}

// ------------------------------------------------------------------ servo
void servoWriteUs(int us) {
  us = constrain(us, SERVO_MID - SERVO_RANGE, SERVO_MID + SERVO_RANGE);
  uint32_t duty = (uint32_t)((uint64_t)us * ((1 << SERVO_BITS) - 1) / (1000000 / SERVO_FREQ));
  pwmWrite(SERVO_PIN, 4, duty);
}

// ------------------------------------------------------------------ accu
float readVbat() {
  uint32_t mv = 0;
  for (int i = 0; i < 8; i++) mv += analogReadMilliVolts(VBAT_PIN);
  return mv / 8.0 / 1000.0 * VBAT_DIVIDER;
}

// ------------------------------------------------------------------ Bluepad32
ControllerPtr ctl = nullptr;

void onConnected(ControllerPtr c) {
  if (ctl == nullptr) {
    ctl = c;
    Serial.printf("controller verbonden: %s\n", c->getModelName().c_str());
  } else {
    Serial.println("tweede controller genegeerd");
  }
}

void onDisconnected(ControllerPtr c) {
  if (c == ctl) {
    ctl = nullptr;
    Serial.println("controller weg: motoren uit");
  }
}

int applyDeadzone(int v) {
  if (abs(v) < DEADZONE) return 0;
  return v > 0 ? v - DEADZONE : v + DEADZONE;
}

// ------------------------------------------------------------------ setup / loop
bool lowBattery = false;

void setup() {
  motorInit(motA);                            // eerst de bruggen veilig uit
  motorInit(motB);
  pwmAttach(SERVO_PIN, SERVO_FREQ, SERVO_BITS, 4);
  servoWriteUs(SERVO_MID);

  Serial.begin(115200);
  Serial.printf("DIY-Auto test_drive, MAX_PWM %.0f %%\n", MAX_PWM * 100);
  BP32.setup(&onConnected, &onDisconnected);
  BP32.forgetBluetoothKeys();                 // koppelen: Xbox-knop aan, dan de koppelknop bovenaan ingedrukt houden
  BP32.enableVirtualDevice(false);
}

void loop() {
  BP32.update();

  static uint32_t lastVbat = 0, lowSince = 0, lastPrint = 0;
  if (USE_VBAT_CUTOFF && millis() - lastVbat > 250) {
    lastVbat = millis();
    float v = readVbat();
    if (v < VBAT_MIN) { if (!lowSince) lowSince = millis(); }
    else lowSince = 0;
    if (lowSince && millis() - lowSince > 2000 && !lowBattery) {
      lowBattery = true;
      Serial.printf("accu leeg (%.2f V): motoren uit tot een reset\n", v);
    }
  }

  float throttle = 0, steer = 0;
  bool brake = false;
  if (ctl && ctl->isConnected() && ctl->isGamepad() && !lowBattery) {
    throttle = -applyDeadzone(ctl->axisY()) / (512.0 - DEADZONE);   // joystick omhoog = negatief
    steer    =  applyDeadzone(ctl->axisRX()) / (512.0 - DEADZONE);
    brake    = ctl->b();
    throttle = constrain(throttle, -1.0, 1.0);
    steer    = constrain(steer, -1.0, 1.0);
  }

  motorSet(motA, throttle, brake);
  motorSet(motB, throttle, brake);
  if (STEER_INVERT) steer = -steer;
  servoWriteUs(SERVO_MID + (int)(steer * SERVO_RANGE));

  if (millis() - lastPrint > 200) {
    lastPrint = millis();
    Serial.printf("gas %+.2f  stuur %+.2f  rem %d  A %d  B %d%s\n", throttle, steer, brake, motA.dir, motB.dir,
                  ctl ? "" : "  (geen controller)");
  }
  delay(5);
}
