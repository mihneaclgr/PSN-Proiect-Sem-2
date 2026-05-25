#include <EEPROM.h>
#include <DHT.h>

const int LED_PIN = 13;
#define DHTPIN 2
#define DHTTYPE DHT11

DHT dht(DHTPIN, DHTTYPE);
int msgIndex = 0;
unsigned long lastRead = 0;

void sendEEPROM() {
  for (int slot = 0; slot < 10; slot++) {
    Serial.print("MSG:");
    Serial.print(slot);
    Serial.print(":");
    for (int i = 0; i < 20; i++) {
      char c = EEPROM.read(slot * 20 + i);
      if (c == '\0') break;
      Serial.print(c);
    }
    Serial.println();
  }
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  Serial.println("READY");
}

void loop() {
  if (millis() - lastRead >= 1000) {
    float h = dht.readHumidity();
    float t = dht.readTemperature();
    if (!isnan(t) && !isnan(h)) {
      Serial.print("TEMP:");
      Serial.println(t, 1);
      Serial.print("HUM:");
      Serial.println(h, 1);
    }
    
    Serial.print("LED_STATE:");
    Serial.println(digitalRead(LED_PIN) == HIGH ? "ON" : "OFF");
    
    lastRead = millis();
  }

  while (Serial.available() > 0) {
    char cmd = Serial.read();
    
    if (cmd == 'A') {
      digitalWrite(LED_PIN, HIGH);
      Serial.println("LED_STATE:ON");
    } else if (cmd == 'S') {
      digitalWrite(LED_PIN, LOW);
      Serial.println("LED_STATE:OFF");
    } else if (cmd == 'M') {
      String msg = Serial.readStringUntil('\n');
      msg.trim(); 
      int addrOffset = msgIndex * 20; 
      
      for(int i = 0; i < msg.length() && i < 19; i++) {
         EEPROM.update(addrOffset + i, msg[i]);
      }
      EEPROM.update(addrOffset + (msg.length() < 19 ? msg.length() : 19), '\0');
      msgIndex = (msgIndex + 1) % 10;
      sendEEPROM();
    } else if (cmd == 'R') {
      sendEEPROM();
    }
  }
}