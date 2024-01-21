#include "FS.h"
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <NTPClient.h>
#include <WiFiUdp.h>
#include <Wire.h>
#include "MAX30100_PulseOximeter.h"

// Update these with values suitable for your network.

const char *ssid="kamat"; 
const char *password="1234kamat";

WiFiUDP ntpUDP;
NTPClient timeClient(ntpUDP, "pool.ntp.org");

const char* AWS_endpoint = "a2y9prqvlyko4a-ats.iot.us-east-2.amazonaws.com"; //MQTT broker ip


void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  for (int i = 0; i < length; i++) {
    Serial.print((char)payload[i]);
  }
  Serial.println();

}

WiFiClientSecure espClient;
PubSubClient client(AWS_endpoint, 8883, callback, espClient); //set  MQTT port number to 8883 as per //standard
#define BUFFER_LEN 256
long lastMsg = 0;
char msg[BUFFER_LEN];
int value = 0;
byte mac[6];
char mac_Id[18];

#define REPORTING_PERIOD_MS     1000

PulseOximeter pox;

void setup_wifi() {
  
  delay(10);
  // We start by connecting to a WiFi network
  
  espClient.setBufferSizes(512, 512);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());

  timeClient.begin();
  
  while(!timeClient.update()){
    timeClient.forceUpdate();
  }

  espClient.setX509Time(timeClient.getEpochTime());

}


void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Attempt to connect
    if (client.connect("TestThing")) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      //client.publish("outTopic","hello");
      // ... and resubscribe
      client.subscribe("inTopic");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");

      char buf[256];
      espClient.getLastSSLError(buf,256);
      Serial.print("WiFiClientSecure SSL error: ");
      Serial.println(buf);

      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}


void setup() {
  
  Serial.begin(115200);
  Serial.setDebugOutput(true);

  pox.begin();
  
  setup_wifi();
  delay(1000);
  
  if (!SPIFFS.begin()) {
    Serial.println("Failed to mount file system");
    return;
  }

  Serial.print("Heap: "); Serial.println(ESP.getFreeHeap());

  // Load certificate file
  File cert = SPIFFS.open("/cert.der", "r"); //replace cert.crt with your uploaded file name
  if (!cert) {
    Serial.println("Failed to open cert file");
  }
  else
    Serial.println("Success to open cert file");

  delay(1000);

  if (espClient.loadCertificate(cert))
    Serial.println("cert loaded");
  else
    Serial.println("cert not loaded");
    

  // Load private key file
  File private_key = SPIFFS.open("/private.der", "r"); //replace private with your uploaded file name
  if (!private_key) {
    Serial.println("Failed to open private cert file");
  }
  else
    Serial.println("Success to open private cert file");

  delay(1000);

  if (espClient.loadPrivateKey(private_key))
    Serial.println("private key loaded");
  else
    Serial.println("private key not loaded");
    

   // Load CA file
  File ca = SPIFFS.open("/ca.der", "r"); //replace ca eith your uploaded file name
  if (!ca) {
    Serial.println("Failed to open ca ");
  }
  else
    Serial.println("Success to open ca");

    delay(1000);

    if(espClient.loadCACert(ca))
      Serial.println("ca loaded");
    else
      Serial.println("ca failed");
      Serial.print("Heap: "); Serial.println(ESP.getFreeHeap());

    
    WiFi.macAddress(mac);
    snprintf(mac_Id, sizeof(mac_Id), "%02x:%02x:%02x:%02x:%02x:%02x",
    mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    Serial.print(mac_Id);

}

void loop() {

  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  pox.update();
  
  long now = millis();
  if (now - lastMsg > 1000) {
    lastMsg = now;
    
    String macIdStr = mac_Id;
    float p = pox.getHeartRate();      // Get heart rate reading
    delay(10);
    float s = pox.getSpO2();   // Get spo2 reading
    snprintf (msg, BUFFER_LEN, "{\"mac_Id\" : \"%s\", \"Pulse_Rate\" : %f, \"Spo2\" : %f}", macIdStr.c_str(), p, s);

    Serial.print("Publish message: ");
    Serial.println(msg);
    client.publish("Pulse_Oximeter", msg);
    Serial.print("Heap: "); Serial.println(ESP.getFreeHeap()); //Low heap can cause problems
  }
}
