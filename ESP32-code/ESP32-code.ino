#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>
#include <OneWire.h>

#define TEMP 25
#define PH 26
#define TURBIDITY 27
#define TDS 14

#define TEMP_ERROR 21
#define PH_ERROR 19
#define TURB_ERROR 18
#define TDS_ERROR 5

const char* DEVICE_LOGIN_NAME  = "44f23f80-3e5e-43a7-b951-9fc88ba0c229"; // MAC address of arduino
const char* SSID     = "MyResNet-2G"; // SSID for ResNet 2GHz network
const char* PASSWORD = "Goldenrod-Ghana-65!"; // needs a password for the Union 2G network
const char* DEVICE_KEY = "rd7oYlVimFoGAJADPzt7XD65T"; // not-so-secret key for my arduino

float temperature;
float pH;
float turbidity;
float tds;

OneWire ds(TEMP);

void initPins(){

  pinMode(TEMP, INPUT);
  pinMode(PH, INPUT);
  pinMode(TURBIDITY, INPUT);
  pinMode(TDS, INPUT);

  pinMode(TEMP_ERROR, OUTPUT);
  pinMode(PH_ERROR, OUTPUT);
  pinMode(TURB_ERROR, OUTPUT);
  pinMode(TDS_ERROR, OUTPUT);

}

void initArduinoCloud(){

  ArduinoCloud.setBoardId(DEVICE_LOGIN_NAME);
  ArduinoCloud.setSecretDeviceKey(DEVICE_KEY);

  ArduinoCloud.addProperty(pH, READ, 30 * SECONDS, NULL);
  ArduinoCloud.addProperty(tds, READ, 30 * SECONDS, NULL);
  ArduinoCloud.addProperty(temperature, READ, 30 * SECONDS, NULL);
  ArduinoCloud.addProperty(turbidity, READ, 30 * SECONDS, NULL);

  WiFiConnectionHandler ArduinoIoTPreferredConnection(SSID, PASSWORD);

  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

}


void setup() {

  Serial.begin(115200);
  delay(1500);

  initPins();
  
  initArduinoCloud();

  

}

void loop() {

  ArduinoCloud.update();

  // Using boolean return since the variables are set at in the read() functions
  // True means read was successful so no warning light, False does the opposite
  // May want to revisit this logic to see about CPU overhead so we draw less power

  if (!readTemp) {
    digitalWrite(TEMP_ERROR, HIGH);
    Serial.println("Temp Failure!");
  }
  if (!readPH) {
    digitalWrite(PH_ERROR, HIGH);
  }
  if (!readTurbidity) {
    digitalWrite(TURB_ERROR, HIGH);
  }
  if (!readTDS) {
    digitalWrite(TDS_ERROR, HIGH);
  }

  delay(3000); // we may want to look into delay methods that are less power consuming since this just cycles the CPU

}



bool readTemp() {
  //returns the temperature from one DS18S20 in DEG Celsius

  byte data[12];
  byte addr[8];

  if ( !ds.search(addr)) {
      //no more sensors on chain, reset search
      Serial.println("no more sensors on chain, reset search!");
      ds.reset_search();
      return false;
  }

  if ( OneWire::crc8( addr, 7) != addr[7]) {
      Serial.println("CRC is not valid!");
      return false;
  }

  if ( addr[0] != 0x10 && addr[0] != 0x28) {
      Serial.print("Device is not recognized");
      return false;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44,1); // start conversion, with parasite power on at the end

  byte present = ds.reset();
  ds.select(addr);
  ds.write(0xBE); // Read Scratchpad


  for (int i = 0; i < 9; i++) { // we need 9 bytes
    data[i] = ds.read();
  }

  ds.reset_search();

  byte MSB = data[1];
  byte LSB = data[0];

  float tempRead = ((MSB << 8) | LSB); //using two's compliment
  float TemperatureSum = tempRead / 16;

  temperature = TemperatureSum;

  Serial.println(temperature);
  return true;
}


bool readPH() {
  pH = 0;
  return -1;
}

bool readTurbidity() {
  turbidity = 0;
  return -1;
}

bool readTDS(){
  tds = 0;
  return -1;
}


