#include <ArduinoIoTCloud.h>
#include <Arduino_ConnectionHandler.h>
#include <OneWire.h>
#include <math.h>

#define TEMP       25
#define PH         35
#define TURBIDITY  32
#define TDS        33

const char* DEVICE_LOGIN_NAME = "44f23f80-3e5e-43a7-b951-9fc88ba0c229";
const char* SSID              = "MyResNet-2G";
const char* PASSWORD          = "Goldenrod-Ghana-65!";
const char* DEVICE_KEY        = "rd7oYlVimFoGAJADPzt7XD65T";

WiFiConnectionHandler ArduinoIoTPreferredConnection(SSID, PASSWORD);

// Cloud-published globals
float temperature;
float pH;
float turbidity;
float tds;

bool temp_success;
bool pH_success;
bool turb_success;
bool tds_success;

OneWire ds(TEMP);

// Moving average buffer definitions
static const uint8_t BUF_SIZE = 30;

// Temperature buffer state
float tempBuf[BUF_SIZE];
uint8_t tempIdx   = 0;
uint8_t tempCount = 0;
float   tempSum   = 0;

// pH buffer state
float phBuf[BUF_SIZE];
uint8_t phIdx   = 0;
uint8_t phCount = 0;
float   phSum   = 0;

// Turbidity buffer state
float turbBuf[BUF_SIZE];
uint8_t turbIdx   = 0;
uint8_t turbCount = 0;
float   turbSum   = 0;

// TDS buffer state
float tdsBuf[BUF_SIZE];
uint8_t tdsIdx   = 0;
uint8_t tdsCount = 0;
float   tdsSum   = 0;

// Round to N decimal places
float roundTo(float value, uint8_t decimals) {
  float factor = pow(10.0f, decimals);
  return roundf(value * factor) / factor;
}

// Push newVal into circular buffer, update sum/count, return average
float pushAndAvg(float buf[], uint8_t &idx, uint8_t &count, float &sum, float newVal) {
  if (count < BUF_SIZE) {
    buf[count++] = newVal;
    sum += newVal;
  } else {
    sum      -= buf[idx];
    buf[idx]  = newVal;
    sum      += newVal;
  }
  idx = (idx + 1) % BUF_SIZE;
  return sum / count;
}

void setup() {

  Serial.begin(115200);
  delay(5000);

  ArduinoCloud.setBoardId(DEVICE_LOGIN_NAME);
  ArduinoCloud.setSecretDeviceKey(DEVICE_KEY);

  ArduinoCloud.addProperty(pH,          READ, 10 * SECONDS, NULL);
  ArduinoCloud.addProperty(tds,         READ, 10 * SECONDS, NULL);
  ArduinoCloud.addProperty(temperature, READ, 10 * SECONDS, NULL);
  ArduinoCloud.addProperty(turbidity,   READ, 10 * SECONDS, NULL);

  ArduinoCloud.addProperty(pH_success,   READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(tds_success,  READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(temp_success, READ, ON_CHANGE, NULL);
  ArduinoCloud.addProperty(turb_success, READ, ON_CHANGE, NULL);

  ArduinoCloud.begin(ArduinoIoTPreferredConnection);
  setDebugMessageLevel(2);
  ArduinoCloud.printDebugInfo();

  pinMode(TEMP, INPUT);
  pinMode(PH, INPUT);
  pinMode(TURBIDITY, INPUT);
  pinMode(TDS, INPUT);
}

void loop() {

  ArduinoCloud.update();

  temp_success  = readTemp();
  pH_success    = readPH();
  turb_success  = readTurbidity();
  tds_success   = readTDS();

  delay(1000);
}

bool readTemp() {
  byte data[12], addr[8];
  if (!ds.search(addr) || OneWire::crc8(addr, 7) != addr[7] ||
      (addr[0] != 0x10 && addr[0] != 0x28)) {
    temperature = 0;
    return false;
  }

  ds.reset();
  ds.select(addr);
  ds.write(0x44, 1);
  ds.reset();
  ds.select(addr);
  ds.write(0xBE);
  for (int i = 0; i < 9; i++) data[i] = ds.read();
  ds.reset_search();

  float raw = ((data[1] << 8) | data[0]) / 16.0f;
  float avg = pushAndAvg(tempBuf, tempIdx, tempCount, tempSum, raw);
  temperature = roundTo(avg, 2);
  return true;
}

bool readPH() {
  const float offset = 16.3f, slope = 8.3312f;
  float rawV = analogRead(PH) * 5.0f / 4096.0f;
  float val  = rawV * slope - offset;
  if (val < 5 || val > 10) {
    pH = 0;
    return false;
  }
  float avg = pushAndAvg(phBuf, phIdx, phCount, phSum, val);
  pH = roundTo(avg, 2);
  return true;
}

bool readTurbidity() {
  uint16_t a = analogRead(TURBIDITY);
  if (a == 0) {
    turbidity = 0;
    return false;
  }
  float raw = (a * (4.0f/4095.0f) - 4.0f) / -0.0008f;
  raw = max(0.0f, raw);
  float avg = pushAndAvg(turbBuf, turbIdx, turbCount, turbSum, raw);
  turbidity = roundTo(avg, 2);
  return true;
}

bool readTDS() {
  int a = analogRead(TDS);
  float volts = a * (2.3f/4095.0f);
  float coeff = 1.0f + 0.02f * (temperature - 25.0f);
  float raw   = (133.42f*volts*volts*volts
                -255.86f*volts*volts
                +857.39f*volts) * 0.5f / coeff;
  float avg = pushAndAvg(tdsBuf, tdsIdx, tdsCount, tdsSum, raw);
  tds = roundTo(avg, 2);
  return true;
}
