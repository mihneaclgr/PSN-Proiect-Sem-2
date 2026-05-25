#include <EEPROM.h>
#include <DHT.h>

const int LED_PIN = 13;
const int WATER_PIN = 3;
#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
int msgIndex = 0;
int floodIndex = 0;
unsigned long lastRead = 0;
bool lastWaterState = HIGH;

void sendEEPROM() {
  for (int slot = 0; slot < 10; slot++) {
    Serial.print("MSG:"); Serial.print(slot); Serial.print(":");
    for (int i = 0; i < 20; i++) {
      char c = EEPROM.read(slot * 20 + i);
      if (c == '\0') break;
      Serial.print(c);
    }
    Serial.println();
  }
  for (int slot = 0; slot < 10; slot++) {
    Serial.print("FLD:"); Serial.print(slot); Serial.print(":");
    Serial.println(EEPROM.read(200 + slot));
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(LED_PIN, OUTPUT);
  pinMode(WATER_PIN, INPUT_PULLUP);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  if (millis() - lastRead >= 1000) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (!isnan(t) && !isnan(h)) {
      Serial.print("TEMP:"); Serial.println(t, 1);
      Serial.print("HUM:"); Serial.println(h, 1);
    }
    Serial.print("LED_STATE:"); Serial.println(digitalRead(LED_PIN) == HIGH ? "ON" : "OFF");
    lastRead = millis();
  }

  bool currentWaterState = digitalRead(WATER_PIN);
  if (currentWaterState == LOW && lastWaterState == HIGH) {
    Serial.println("FLOOD_EVENT");
    EEPROM.update(200 + floodIndex, 1);
    floodIndex = (floodIndex + 1) % 10;
    sendEEPROM();
    delay(500); 
  }
  lastWaterState = currentWaterState;

  while (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'A') {
      digitalWrite(LED_PIN, HIGH); Serial.println("LED_STATE:ON");
    } else if (cmd == 'S') {
      digitalWrite(LED_PIN, LOW); Serial.println("LED_STATE:OFF");
    } else if (cmd == 'M') {
      String msg = Serial.readStringUntil('\n'); msg.trim();
      int addr = msgIndex * 20;
      for(int i=0; i<msg.length() && i<19; i++) EEPROM.update(addr+i, msg[i]);
      EEPROM.update(addr + (msg.length() < 19 ? msg.length() : 19), '\0');
      msgIndex = (msgIndex + 1) % 10;
      sendEEPROM();
    } else if (cmd == 'R') {
      sendEEPROM();
    } else if (cmd == 'D') {
      int id = Serial.parseInt();
      if (id >= 0 && id <= 9) {
        EEPROM.update(200 + id, 0);
        sendEEPROM();
      }
    }
  }
}