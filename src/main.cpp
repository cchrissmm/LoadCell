#include <Wire.h> //Needed for I2C to GPS
#include <EEPROM.h>
#include "SparkFun_u-blox_GNSS_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_u-blox_GNSS
#include "HX711.h"
#include <SparkFun_ADXL345.h> 
#include <Arduino.h>
#include <string.h>
using std::string;    // this eliminates the need to write std::string, you can just write string
using std::to_string; // this eliminates the need to write std::to_string, you can just write to_string

#define LC_DOUT 4 // LOADCELL
#define LC_CLK 2  // LOADCELL
#define GPS_SDA 22 // GPS
#define GPS_SCL 23 // GPS
#define GPS_NAVFREQ 20

HX711 scale;
SFE_UBLOX_GNSS myGNSS;

float IMU_Roll = 999;
float  IMU_Pitch = 999;
float  IMU_Yaw = 999;

int IMU_xAccel = 999999; 
int IMU_yAccel = 999999;
int IMU_zAccel = 999999;

float LC_scaleValue = -34200; // set this default
long LC_offsetValue = 0;
float LC_Force = 9999999;
string message = "";
int systemErrorState = 0; // 0 = no error, 1 = error
int counter = 0;

TwoWire I2Cone = TwoWire(0); //GPS I2C bus

void setup()
{
  Serial.begin(115200);
  Serial.println("Relativity DAQ v1.0.0");
  Serial.println("Setup started............................................");

  EEPROM.begin(512); // Initialize EEPROM with a size of 512 bytes

  if (EEPROM.get(0, LC_scaleValue))
  {
    Serial.print("LC Calibration factor loaded from EEPROM: ");
    Serial.println(LC_scaleValue);
    if (LC_scaleValue < 30000 || LC_scaleValue > 40000)
    {
      Serial.println("ERROR: LC Calibration factor out of range");
      //systemErrorState = 1;
    }
  }
  else
  {
    Serial.print("ERROR: LC Calibration factor not found in EEPROM ");
    Serial.println(LC_scaleValue);
    systemErrorState = 1;
  }

  if (EEPROM.get(4, LC_offsetValue))
  {
    Serial.print("LC Tare value loaded from EEPROM: ");
    Serial.println(LC_offsetValue);
  }
  else
  {
    Serial.print("ERROR: LC Tare value not found in EEPROM");
    systemErrorState = 1;
  }
  
  
  scale.begin(LC_DOUT, LC_CLK);
  scale.set_offset(LC_offsetValue);
  scale.set_scale(LC_scaleValue);
  scale.set_raw_mode(); 
  
  I2Cone.begin(GPS_SDA, GPS_SCL, 400000); // SDA, SCL

  if (myGNSS.begin(I2Cone) == false)
  {
    Serial.println(F("ERROR u-blox GNSS module not detected at I2C address. Please check wiring."));
    systemErrorState = 1;
  }

  myGNSS.setI2COutput(COM_TYPE_UBX); // Set the I2C port to output UBX only (turn off NMEA noise)

  if (myGNSS.setNavigationFrequency(GPS_NAVFREQ))
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

  if (!systemErrorState)
    Serial.println("Setup completed with no errors............................................");
  else
    Serial.println("Setup completed with errors............................................");
}

void loop()
{
  if (Serial.available())
  {
    String str = Serial.readStringUntil('\n');
    Serial.print("Received: ");
    Serial.println(str);

    if (str.startsWith("<LCZero>"))
    {
      scale.tare();                 // Reset the scale to 0
      Serial.print("Scale zeroed, offset value: ");
      LC_offsetValue = scale.get_offset();
      Serial.println(LC_offsetValue);
      EEPROM.put(4, LC_offsetValue);
      EEPROM.commit();
    }

    if (str.startsWith("<LC10kg>")) // 10kg calibration
    {
      scale.calibrate_scale(980,5);
      LC_scaleValue = scale.get_scale();
      Serial.print("Calibration done at 10kg, scale value: ");
      Serial.println(LC_scaleValue);
      EEPROM.put(0, LC_scaleValue);
      EEPROM.commit();
    }

    if (str.startsWith("<resetESP>")) // 10kg calibration
    {
      Serial.print("ESP Will reset");
      //reset the esp32
      ESP.restart();
    }
  }

  long time = millis();
  long GPS_lat = myGNSS.getLatitude();
  long GPS_long = myGNSS.getLongitude();
  long GPS_groundSpeed_mms = myGNSS.getGroundSpeed();
  float GPS_groundSpeed = GPS_groundSpeed_mms * 0.0001;
  long GPS_heading_105 = myGNSS.getHeading();
  float GPS_heading = GPS_heading_105 * 0.000001; // degrees
  int GPS_Seconds = myGNSS.getSecond();
  int GPS_Minutes = myGNSS.getMinute();
  int GPS_Hours = myGNSS.getHour();
  int GPS_Day = myGNSS.getDay();
  int GPS_Month = myGNSS.getMonth();


  if(scale.is_ready()) { // only proceed if HX711 is ready to read
  LC_Force = scale.get_units();
  }

  if (myGNSS.getEsfAlignment(5)) // Poll new ESF ALG data
  {
  IMU_Roll = myGNSS.getESFroll();
  IMU_Pitch = myGNSS.getESFpitch();
  IMU_Yaw = myGNSS.getESFyaw();
  }

if (myGNSS.getEsfIns(5)) // Poll new ESF INS data
  {
    IMU_xAccel = myGNSS.packetUBXESFINS->data.xAccel;  
    IMU_yAccel = myGNSS.packetUBXESFINS->data.yAccel;  
    IMU_zAccel = myGNSS.packetUBXESFINS->data.zAccel;
  }

  if (systemErrorState == 1)
  {
    // Serial.println("ERROR system error");
    // vTaskDelay(10000 / portTICK_PERIOD_MS);
    return;
  }
  else
  {
    counter += 1;

    if(counter > 40) {
    Serial.println("HEADtime,GPS_groundSpeed,GPS_lat,GPS_long,GPS_heading,GPS_Seconds,GPS_Minutes,GPS_Hours,GPS_Day,GPS_Month,LC_Force,IMU_roll,IMU_pitch,IMU_yaw,IMU_xAccel,IMU_yAccel,IMU_zAccel");
    counter = 0;  
  }
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
    Serial.print(GPS_Seconds);
    Serial.print(",");
    Serial.print(GPS_Minutes);
    Serial.print(",");
    Serial.print(GPS_Hours);
    Serial.print(",");
    Serial.print(GPS_Day);
    Serial.print(",");
    Serial.print(GPS_Month);
    Serial.print(",");
    Serial.print(LC_Force);
    Serial.print(",");
    Serial.print(IMU_Roll);
    Serial.print(",");
    Serial.print(IMU_Pitch);
    Serial.print(",");
    Serial.print(IMU_Yaw);
    Serial.print(",");
    Serial.print(IMU_xAccel);
    Serial.print(",");
    Serial.print(IMU_yAccel);
    Serial.print(",");
    Serial.println(IMU_zAccel);
  }
}
