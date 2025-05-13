#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>

#define TEMP 0;
#define PH 0;
#define TURBIDITY 0;
#define TDS 0;

#define TEMP_ERROR 0;
#define PH_ERROR 0;
#define TURB_ERROR 0;
#define TDS_ERROR 0;

const char* DEVICE_LOGIN_NAME  = "44f23f80-3e5e-43a7-b951-9fc88ba0c229"; // MAC address of arduino
const char* SSID     = "MyResNet-2G";
const char* PASSWORD = "**password**"; // needs a password for the Union 2G network
const char* DEVICE_KEY = "rd7oYlVimFoGAJADPzt7XD65T"; // not-so-secret key for my arduino

float temperature;
float pH;
float turbidity;
float tds;

void initArduinoCloud(){

  ArduinoCloud.setBoardId(DEVICE_LOGIN_NAME);
  ArduinoCloud.setSecretDeviceKey(DEVICE_KEY);
  ArduinoCloud.addProperty(motion, READ, ON_CHANGE, NULL);

}

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


void setup() {

  Serial.begin(115200);
  delay(1500);

  initPins();
  
  initArduinoCloud();

  WiFiConnectionHandler ArduinoIoTPreferredConnection(SSID, PASS);

  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  

}

void loop() {

  ArduinoCloud.update();

  // Using boolean return since the variables are set at in the read() functions
  // True means read was successful so no warning light, False does the opposite
  // May want to revisit this logic to see about CPU overhead so we draw less power

  if (!readTemp) {
    digitalWrite(TEMP_ERROR, HIGH);
  }
  if (!readPH) {
    digitalWrite(PH_ERROR, HIGH);
  }
  if (!readTurbidity) {
    digitalWrite(TURB_ERROR, HIGH);
  }

  delay(3000) // we may want to look into delay methods that are less power consuming since this just cycles the CPU

}



bool readTemp() {
  return -1;
}


bool readPH() {
  return -1;
}

bool readTurbidity() {
  return -1;
}

bool readTDS(){
  return -1;
}


