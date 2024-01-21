/*
 Example using the SparkFun HX711 breakout board with a scale
 By: Nathan Seidle
 SparkFun Electronics
 Date: November 19th, 2014
 License: This code is public domain but you buy me a beer if you use this and we meet someday (Beerware license).

 This is the calibration sketch. Use it to determine the calibration_factor that the main example uses. It also
 outputs the zero_factor useful for projects that have a permanent mass on the scale in between power cycles.

 Setup your scale and start the sketch WITHOUT a weight on the scale
 Once readings are displayed place the weight on the scale
 Press +/- or a/z to adjust the calibration_factor until the output readings match the known weight
 Use this calibration_factor on the example sketch

 This example assumes pounds (lbs). If you prefer kilograms, change the Serial.print(" lbs"); line to kg. The
 calibration factor will be significantly different but it will be linearly related to lbs (1 lbs = 0.453592 kg).

 Your calibration factor may be very positive or very negative. It all depends on the setup of your scale system
 and the direction the sensors deflect from zero state
 This example code uses bogde's excellent library: https://github.com/bogde/HX711
 bogde's library is released under a GNU GENERAL PUBLIC LICENSE
 Arduino pin 2 -> HX711 CLK
 3 -> DOUT
 5V -> VCC
 GND -> GND

 Most any pin on the Arduino Uno will be compatible with DOUT/CLK.

 The HX711 board can be powered from 2.7V to 5V so the Arduino 5V power should be fine.

*/

#include <Wire.h> //Needed for I2C to GPS
#include <EEPROM.h>

#include "SparkFun_u-blox_GNSS_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_u-blox_GNSS
SFE_UBLOX_GNSS myGNSS;

#include "HX711.h"
#include <Arduino.h>

#include <string.h>
using std::string;    // this eliminates the need to write std::string, you can just write string
using std::to_string; // this eliminates the need to write std::to_string, you can just write to_string

#define DOUT 2
#define CLK 4

#define GPS_SDA 22
#define GPS_SCL 23

HX711 scale;

float calibration_factor = -34200; // set this default
float tareValue = 0;
string message = "";
int systemErrorState = 0; // 0 = no error, 1 = error

void setup()
{
  Serial.begin(115200);
  Serial.println("Relativity DAQ v1.0.0");
  Serial.println("Setup started............................................");

  scale.begin(DOUT, CLK);

  EEPROM.begin(512); // Initialize EEPROM with a size of 512 bytes

  if (EEPROM.get(0, calibration_factor))
  {
    Serial.print("LC Calibration factor loaded from EEPROM: ");
    Serial.println(calibration_factor);
  }
  else
  {
    Serial.print("ERROR: LC Calibration factor not found in EEPROM, using default: ");
    systemErrorState = 1;
    Serial.println(calibration_factor);
  }

  if (EEPROM.get(4, tareValue))
  {
    Serial.print("LC Tare value loaded from EEPROM: ");
    Serial.println(tareValue);
  }
  else
  {
    Serial.print("ERROR: LC Tare value not found in EEPROM, using default: ");
    systemErrorState = 1;
    Serial.println(tareValue);
  }
  scale.set_offset(tareValue);
  scale.set_scale(calibration_factor);

  Wire.begin(GPS_SDA, GPS_SCL); // SDA, SCL

  if (myGNSS.begin() == false)
  {
    Serial.println(F("ERROR u-blox GNSS module not detected at I2C address. Please check wiring."));
    systemErrorState = 1;
  }

  myGNSS.setI2COutput(COM_TYPE_UBX); // Set the I2C port to output UBX only (turn off NMEA noise)

  if (myGNSS.setNavigationFrequency(30))
  {
    Serial.println(F("Set Nav Frequency Successful"));
  }
  else
  {
    Serial.println(F("ERROR Set Nav Frequency Failed"));
    systemErrorState = 1;
  }

  myGNSS.setESFAutoAlignment(true); // Enable Automatic IMU-mount Alignment

  if (myGNSS.getEsfInfo())
  {

    Serial.print(F("Fusion Mode: "));
    Serial.println(myGNSS.packetUBXESFSTATUS->data.fusionMode);

    if (myGNSS.packetUBXESFSTATUS->data.fusionMode == 1)
    {
      Serial.println(F("Fusion Mode is Initialized!"));
    }
    else
    {
      Serial.println(F("ERROR Fusion Mode is either disabled or not initialized!"));
      systemErrorState = 1;
    }
  }

  Serial.println("Setup complete............................................");
}

void loop()
{
  while (Serial.available())
  {
    char msgBit = Serial.read();
    if (msgBit == '<') // Start of delimiter received
    {
      message = ""; // Reset message buffer
    }
    else if (msgBit == '>') // End of delimiter received
    {
      if (message == "<LCZero>")
      {
        scale.tare(); // Reset the scale to 0
        tareValue = scale.get_tare(); //get the value
        scale.set_offset(tareValue);
        EEPROM.put(4, tareValue);
        EEPROM.commit();
        Serial.print("Scale zeroed: ");
        Serial.println(tareValue);
        vTaskDelay(5000 / portTICK_PERIOD_MS);
      }
      if (message == "<LC10kg>") // 10kg calibration
      {
        float currentValue = scale.get_units(10);
        float calibrationValue = currentValue / 980; // 10Kg = 980 Newtons
        scale.set_scale(calibrationValue);
        EEPROM.put(0, calibrationValue);
        EEPROM.commit();
        Serial.print("Calibration done at 10kg: ");
        Serial.println(calibrationValue);
        vTaskDelay(5000 / portTICK_PERIOD_MS);
      }
      message = ""; // Reset message buffer
    }
    else // Message character received
    {
      message += msgBit;
    }
  }

  long time = millis();
  long GPS_lat = myGNSS.getLatitude();
  long GPS_long = myGNSS.getLongitude();
  long GPS_groundSpeed_mms = myGNSS.getGroundSpeed();
  float GPS_groundSpeed = GPS_groundSpeed_mms * 0.0001;
  long GPS_heading_105 = myGNSS.getHeading();
  float GPS_heading = GPS_heading_105 * 0.000001; // degrees
  long GPS_Seconds = myGNSS.getSecond();
  float LC_Force = (scale.get_units(),3);

  if (systemErrorState == 1)
  {
    Serial.println("ERROR system error");
    vTaskDelay(10000 / portTICK_PERIOD_MS);
    return;
  }
  else
  {
    Serial.println("HEADtime,GPS_groundSpeed,GPS_lat,GPS_long,GPS_heading,GPS_Seconds,LC_Force");
    Serial.print("DATA");
    Serial.print(time);
    Serial.print(",");
    Serial.print(GPS_groundSpeed);
    Serial.print(",");
    Serial.print(GPS_lat);
    Serial.print(",");
    Serial.print(GPS_long);
    Serial.print(",");
    Serial.print(GPS_heading);
    Serial.print(",");
    Serial.println(GPS_Seconds);
    Serial.print(",");
    Serial.println(LC_Force);
  }
}
