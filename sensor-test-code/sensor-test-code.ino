#include <OneWire.h>

#define TEMP 25
#define TURB 27
#define TDS 33

OneWire ds(TEMP);

float temperature;

void setup() {

  pinMode(TEMP, INPUT);
  pinMode(TURB, INPUT);
  pinMode(TDS, INPUT);

  Serial.begin(115200);
  delay(1500);

}

void loop() {

  bool success;
  int tds;

  delay(3000);

  //success = readTemp();

  //success = readTurb();

  tds = readTDS();

}

bool readTemp(){

   //returns the temperature from one DS18S20 in DEG Celsius

  byte data[12];
  byte addr[8];

  if ( !ds.search(addr)) {
      //no more sensors on chain, reset search
      Serial.println("no more sensors on chain, reset search!");
      ds.reset_search();
      Serial.println("failure");
      return false;
  }

  if ( OneWire::crc8( addr, 7) != addr[7]) {
      Serial.println("CRC is not valid!");
      Serial.println("failure");
      return false;
  }

  if ( addr[0] != 0x10 && addr[0] != 0x28) {
      Serial.print("Device is not recognized");
      Serial.println("failure");
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

bool readTurb(){

  float turb;

  int sensorValue = analogRead(TURB);// read the input on analog pin 0:

  Serial.println(sensorValue);

  turb = sensorValue * (4.0 / 1024); // Convert the analog reading (which goes from 0 - 1023) to a voltage (0 - 5V):

  Serial.println(turb); // print out the value you read:


  return true;

}

float readTDS() {

  float td = analogRead(TDS);
  Serial.println(td);

  return td;
}