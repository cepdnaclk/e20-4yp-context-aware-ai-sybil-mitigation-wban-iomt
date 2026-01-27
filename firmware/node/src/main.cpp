#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include "secrets.h"

// Build-time configuration from platformio.ini
#ifndef NODE_ID
  #error "NODE_ID is not defined (set in platformio.ini build_flags)"
#endif

#ifndef MSG_TYPE
  #error "MSG_TYPE is not defined (set in platformio.ini build_flags)"
#endif

#ifndef TX_PERIOD_MS
  #error "TX_PERIOD_MS is not defined (set in platformio.ini build_flags)"
#endif

#ifndef GATEWAY_IP
  #error "GATEWAY_IP is not defined (set in platformio.ini build_flags)"
#endif

#ifndef GATEWAY_PORT
  #error "GATEWAY_PORT is not defined (set in platformio.ini build_flags)"
#endif

WiFiUDP udp;

static uint16_t boot_id = 0;
static uint32_t seq_counter = 0;

static unsigned long last_send_ms = 0;

void connect_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  Serial.print("[WiFi] Connecting");
  const unsigned long start = millis();
  const unsigned long timeout_ms = 20000;

  while (WiFi.status() != WL_CONNECTED && (millis() - start) < timeout_ms) {
    delay(250);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.print("[WiFi] Connected. IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println();
    Serial.println("[WiFi] Connection timeout. Will retry in loop.");
  }
}

void setup() {
  Serial.begin(115200);
  delay(200);

  // Generate boot_id (uint16)
  // Prefer hardware RNG when available:
  boot_id = (uint16_t)esp_random();

  Serial.println();
  Serial.println("=== WBAN Node (Phase A) ===");
  Serial.print("NODE_ID      : "); Serial.println(NODE_ID);
  Serial.print("MSG_TYPE     : "); Serial.println(MSG_TYPE);
  Serial.print("TX_PERIOD_MS : "); Serial.println(TX_PERIOD_MS);
  Serial.print("GATEWAY_IP   : "); Serial.println(GATEWAY_IP);
  Serial.print("GATEWAY_PORT : "); Serial.println(GATEWAY_PORT);
  Serial.print("BOOT_ID      : "); Serial.println(boot_id);

  connect_wifi();

  // UDP doesn't need begin() for sending, but it's fine to set a local port if desired.
  // udp.begin(0);
  last_send_ms = millis();
}

void loop() {
  // Reconnect Wi-Fi if dropped
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long last_retry = 0;
    if (millis() - last_retry > 3000) {
      last_retry = millis();
      Serial.println("[WiFi] Disconnected. Reconnecting...");
      connect_wifi();
    }
    delay(10);
    return;
  }

  const unsigned long now = millis();
  if (now - last_send_ms >= (unsigned long)TX_PERIOD_MS) {
    last_send_ms = now;

    // Payload format: node_id,boot_id,seq,msg_type
    // Example: ecg_01,41237,1024,ECG
    char payload[96];
    snprintf(payload, sizeof(payload), "%s,%u,%lu,%s",
             NODE_ID,
             (unsigned int)boot_id,
             (unsigned long)seq_counter,
             MSG_TYPE);

    udp.beginPacket(GATEWAY_IP, (uint16_t)GATEWAY_PORT);
    udp.write((const uint8_t*)payload, strlen(payload));
    udp.endPacket();

    // Optional: print occasionally (avoid flooding Serial)
    if ((seq_counter % 50) == 0) {
      Serial.print("[TX] seq=");
      Serial.print(seq_counter);
      Serial.print(" payload=");
      Serial.println(payload);
    }

    seq_counter++;
  }

  delay(1);
}
