#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>
#include <OneWire.h>

#define TEMP 25
#define PH 35
#define TURBIDITY 32
#define TDS 33

const char* DEVICE_LOGIN_NAME  = "44f23f80-3e5e-43a7-b951-9fc88ba0c229"; // MAC address of arduino
const char* SSID     = "MyResNet-2G"; // SSID for ResNet 2GHz network
const char* PASSWORD = "Goldenrod-Ghana-65!"; // needs a password for the Union 2G network
const char* DEVICE_KEY = "rd7oYlVimFoGAJADPzt7XD65T"; // not-so-secret key for my arduino

const unsigned long READ_INTERVAL = 3000;
unsigned long lastReadMillis = 0;

WiFiConnectionHandler ArduinoIoTPreferredConnection(SSID, PASSWORD);

float temperature;
float pH;
float turbidity;
float tds;

bool temp_error;
bool pH_error;
bool turb_error;
bool tds_error;

OneWire ds(TEMP);

void setup() {

  Serial.begin(115200);
  delay(5000);

  pinMode(TEMP, INPUT);
  pinMode(PH, INPUT);
  pinMode(TURBIDITY, INPUT);
  pinMode(TDS, INPUT);
  
  ArduinoCloud.setBoardId(DEVICE_LOGIN_NAME);
  ArduinoCloud.setSecretDeviceKey(DEVICE_KEY);

  ArduinoCloud.addProperty(pH, READ, 30 * SECONDS, NULL);
  ArduinoCloud.addProperty(tds, READ, 30 * SECONDS, NULL);
  ArduinoCloud.addProperty(temperature, READ, 30 * SECONDS, NULL);
  ArduinoCloud.addProperty(turbidity, READ, 30 * SECONDS, NULL);

  ArduinoCloud.addProperty(pH_error, READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(tds_error, READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(temp_error, READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(turb_error, READ, ON_CHANGE, NULL);

  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  Serial.println();
  Serial.println("=== Sensor Menu ===");
  Serial.println("Press 1 → Temperature");
  Serial.println("Press 2 → pH");
  Serial.println("Press 3 → Turbidity");
  Serial.println("Press 4 → TDS");
  Serial.println("===================");
  Serial.println();  

}

void loop() {

  ArduinoCloud.update();

  // Using boolean return since the variables are set at in the read() functions
  // True means read was successful so no warning light, False does the opposite
  // May want to revisit this logic to see about CPU overhead so we draw less power

  unsigned long now = millis();
  // every READ_INTERVAL ms, refresh all four sensors in the background
  if (now - lastReadMillis >= READ_INTERVAL) {
    lastReadMillis = now;
    temp_error  = readTemp(); // needs to be true if reading successful, false if unsuccessful due to dashboard LEDs
    pH_error    = readPH();
    turb_error  = readTurbidity();
    tds_error   = readTDS();
  }

   if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case '1':
        if (!temp_error) {
          Serial.println("Temp read failed");
        } else {
          Serial.print("Temp----Value: ");
          Serial.print(temperature, 0);
          Serial.println("°C");
        }
        break;

      case '2':
        if (!pH_error) {
          Serial.println("pH read failed");
        } else {
          Serial.print("pH----Value: ");
          Serial.println(pH, 0);
        }
        break;

      case '3':
        if (!turb_error) {
          Serial.println("Turbidity read failed");
        } else {
          Serial.print("Turbidity----Value: ");
          Serial.print(turbidity, 0);
          Serial.println("NTU");
        }
        break;

      case '4':
        if (!tds_error) {
          Serial.println("TDS read failed");
        } else {
          Serial.print("TDS----Value: ");
          Serial.print(tds, 0);
          Serial.println("ppm");
        }
        break;

      default:
        // ignore other characters
        break;
    }
   }

}



bool readTemp() {
  //returns the temperature from one DS18S20 in DEG Celsius

  byte data[12];
  byte addr[8];

  if ( !ds.search(addr)) {
      return false;
  }

  if ( OneWire::crc8( addr, 7) != addr[7]) {
      return false;
  }

  if ( addr[0] != 0x10 && addr[0] != 0x28) {
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

  return true;
}


bool readPH() {

  float pHValue = analogRead(PH);

  Serial.print("    pH value: ");
  Serial.println(pHValue,2);

  pH = pHValue;
  return true;
}

bool readTurbidity() {

  uint16_t analog = analogRead(TURBIDITY);

  if (analog == 0) return true;

  float volts = analog * (4.0f / 4095.0f);

  turbidity = (volts - 4.0) / (-0.0008); // Convert the analog voltage to turbidity: https://iopscience.iop.org/article/10.1088/1742-6596/1280/2/022064/pdf

  return true;
}

bool readTDS(){
  int analog = analogRead(TDS);

  float volts = analog * (2.3f / 4095.0f);

  float compensationCoefficient = 1.0 + 0.02 * (temperature - 25.0);
  float compensationVolatge = volts / compensationCoefficient;

  tds = (133.42 * compensationVolatge * compensationVolatge * compensationVolatge - 255.86 * compensationVolatge * compensationVolatge + 857.39 * compensationVolatge) * 0.5;
  // http://www.cqrobot.wiki/index.php/TDS_(Total_Dissolved_Solids)_Meter_Sensor_SKU:_CQRSENTDS01

  return true;
}


