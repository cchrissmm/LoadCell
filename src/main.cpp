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

#include "SparkFun_u-blox_GNSS_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_u-blox_GNSS
SFE_UBLOX_GNSS myGNSS;

#include "HX711.h"
#include <Arduino.h>

#define DOUT  2
#define CLK  4

#define GPS_SDA 22
#define GPS_SCL 23

HX711 scale;

float calibration_factor = -34200; //-7050 worked for my 440lb max scale setup

void setup() {
  Serial.begin(115200);
  Serial.println("HX711 calibration sketch");
  Serial.println("Remove all weight from scale");
  Serial.println("After readings begin, place known weight on scale");
  Serial.println("Press + or a to increase calibration factor");
  Serial.println("Press - or z to decrease calibration factor");

  scale.begin(DOUT, CLK);
  scale.set_scale();
  scale.tare(); //Reset the scale to 0

  long zero_factor = scale.read_average(); //Get a baseline reading
  Serial.print("Zero factor: "); //This can be used to remove the need to tare the scale. Useful in permanent scale projects.
  Serial.println(zero_factor);

  Wire.begin(GPS_SDA,GPS_SCL);  //SDA, SCL

  if (myGNSS.begin() == false)
  {
    Serial.println(F("u-blox GNSS module not detected at default I2C address. Please check wiring. Freezing."));
    while (1);
  }

  //This will pipe all NMEA sentences to the serial port so we can see them
  //myGNSS.setNMEAOutputPort(Serial);

  myGNSS.setI2COutput(COM_TYPE_UBX); //Set the I2C port to output UBX only (turn off NMEA noise)

  if(myGNSS.setNavigationFrequency(20)) {
    Serial.println(F("Set Nav Frequency Successful"));
  } else {
    Serial.println(F("Set Nav Frequency Failed"));
  }

  myGNSS.setESFAutoAlignment(true); //Enable Automatic IMU-mount Alignment

  if (myGNSS.getEsfInfo()){

    Serial.print(F("Fusion Mode: "));  
    Serial.println(myGNSS.packetUBXESFSTATUS->data.fusionMode);  

    if (myGNSS.packetUBXESFSTATUS->data.fusionMode == 1){
      Serial.println(F("Fusion Mode is Initialized!"));  
		}
		else {
      Serial.println(F("Fusion Mode is either disabled or not initialized!"));  
			Serial.println(F("Please see the previous example for more information."));
		}
  }
}

void loop() {

  scale.set_scale(calibration_factor); //Adjust to this calibration factor

  // Serial.print("Reading: ");
  // Serial.print(scale.get_units(), 3);
  // Serial.print(" kg"); //Change this to kg and re-adjust the calibration factor if you follow SI units like a sane person
  // Serial.print(" calibration_factor: ");
  // Serial.print(calibration_factor);
  // Serial.println();

  if(Serial.available())
  {
    char temp = Serial.read();
    if(temp == '+' || temp == 'a')
      calibration_factor += 100;
    else if(temp == '-' || temp == 'z')
      calibration_factor -= 100;
  }

  Serial.print(F("Vehicle Attitude Roll:")); 
  Serial.print(myGNSS.getATTroll(), 2); // Use the helper function to get the roll in degrees
  Serial.println(";"); // Use the helper function to get the roll in degrees

  Serial.print(F("Vehicle Attitude Pitch:")); 
  Serial.print(myGNSS.getATTpitch(), 2); // Use the helper function to get the roll in degrees
  Serial.println(";"); // Use the helper function to get the roll in degrees
  delay(25); //Don't pound too hard on the I2C bus
}
