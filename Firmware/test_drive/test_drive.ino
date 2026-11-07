// DIY-Auto — testfirmware: rijden en sturen met een Xbox-controller (Bluepad32).
//
// Board: "ESP32 Dev Module" uit het Bluepad32-boardpakket (esp32_bluepad32), zie [[DIY Auto]] → Firmware.
// Pinnen volgen het KiCad-schema rev 4 (TB6612FNG-module). Voor de eigen H-bruggen op het breadboard: test_drive_hbrug.
//   motor A (links):  AIN1 25, AIN2 26, PWMA 27
//   motor B (rechts): BIN1 32, BIN2 33, PWMB 4
//   STBY 18 (laag = driver uit), servo 19, accumeting 34
//
// Besturing:
//   linkerjoystick Y  = gas (vooruit / achteruit), beide motoren
//   rechterjoystick X = sturen (servo)
//   B ingedrukt       = remmen (IN1 = IN2 = 1)
//   controller weg     = motoren uit, servo in het midden
//
// Stuurtabel TB6612 (per motor):
//   - Vooruit: IN1 = 1, IN2 = 0, PWM = snelheid.  Achteruit: IN1 = 0, IN2 = 1.
//   - Remmen: IN1 = IN2 = 1.  Uitrollen: IN1 = IN2 = 0.
//   - De dead-time zit in de chip: kortsluiting via de code kan niet meer.

#include <Bluepad32.h>

// ------------------------------------------------------------------ instellingen
const float MAX_PWM        = 0.70;   // 3–6 V-motoren op 7,4 V: 70 % ≈ 5,2 V gemiddeld
const bool  MOTOR_B_INVERT = true;   // motor B zit gespiegeld; draait hij verkeerd om, zet dit op false
const bool  MOTOR_A_INVERT = false;
const int   DEADZONE       = 40;     // joystick -511..512
const bool  USE_VBAT_CUTOFF = false; // true zodra R41/R42 er zitten (op het breadboard niet: GPIO34 zweeft)
const float VBAT_MIN       = 6.4;    // V, 3,2 V per cel
const float VBAT_DIVIDER   = 25.1 / 5.1;   // R41 20k, R42 5k1

const int PWM_FREQ = 20000;          // Hz, boven het hoorbare: geen gezoem (TB6612 tot 100 kHz)
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

// ------------------------------------------------------------------ TB6612
const int STBY_PIN = 18;

struct Motor {
  const char* name;
  int in1, in2, pwm;       // pinnen
  int ch;                  // LEDC-kanaal (alleen arduino-esp32 2.x)
  bool invert;
  int dir;                 // -1 achteruit, 0 uit, +1 vooruit, 2 remmen
};

Motor motA = {"A", 25, 26, 27, 0, MOTOR_A_INVERT, 0};
Motor motB = {"B", 32, 33, 4, 1, MOTOR_B_INVERT, 0};

// eigen prototypes: anders zet Arduino ze boven struct Motor en compileert het niet
void motorInit(Motor& m);
void motorSet(Motor& m, float speed, bool brake);

void motorInit(Motor& m) {
  digitalWrite(m.in1, LOW); pinMode(m.in1, OUTPUT);
  digitalWrite(m.in2, LOW); pinMode(m.in2, OUTPUT);
  pwmAttach(m.pwm, PWM_FREQ, PWM_BITS, m.ch);
  pwmWrite(m.pwm, m.ch, 0);
  m.dir = 0;
}

// speed -1..+1; brake = beide uitgangen naar GND
void motorSet(Motor& m, float speed, bool brake) {
  if (m.invert) speed = -speed;
  int want = brake ? 2 : (speed > 0.01 ? 1 : (speed < -0.01 ? -1 : 0));
  uint32_t duty = (uint32_t)(fabsf(speed) * MAX_PWM * PWM_MAX);
  switch (want) {
    case 1:  digitalWrite(m.in1, HIGH); digitalWrite(m.in2, LOW);  break;   // vooruit
    case -1: digitalWrite(m.in1, LOW);  digitalWrite(m.in2, HIGH); break;   // achteruit
    case 2:  digitalWrite(m.in1, HIGH); digitalWrite(m.in2, HIGH); duty = PWM_MAX; break;   // remmen
    default: digitalWrite(m.in1, LOW);  digitalWrite(m.in2, LOW);  duty = 0; break;         // uitrollen
  }
  pwmWrite(m.pwm, m.ch, duty);
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
  digitalWrite(STBY_PIN, LOW); pinMode(STBY_PIN, OUTPUT);   // driver uit tot alles klaarstaat
  motorInit(motA);
  motorInit(motB);
  digitalWrite(STBY_PIN, HIGH);
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
