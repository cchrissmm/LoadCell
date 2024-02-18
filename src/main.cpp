#include <Wire.h> //Needed for I2C to GPS
#include <EEPROM.h>
#include "SparkFun_u-blox_GNSS_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_u-blox_GNSS
#include "HX711.h"
#include <SparkFun_ADXL345.h>
#include <Arduino.h>
#include "ELMo.h"
#include <string.h>
using std::string;    // this eliminates the need to write std::string, you can just write string
using std::to_string; // this eliminates the need to write std::to_string, you can just write to_string


#define LC_DOUT 4  // LOADCELL
#define LC_CLK 2   // LOADCELL
#define GPS_SDA 22 // GPS
#define GPS_SCL 23 // GPS
#define GPS_NAVFREQ 20
#define ADXL_SDA 25   // ADXL345
#define ADXL_SCL 26   // ADXL345
#define ADXL_RANGE 16 // 2,4,8,16

HX711 scale;
SFE_UBLOX_GNSS myGNSS;
ADXL345 adxl_1 = ADXL345(0x53);
ADXL345 adxl_2 = ADXL345(0x1D);
ELMo ELM;

float IMU_Roll = INT_MAX;
float IMU_Pitch = INT_MAX;
float IMU_Yaw = INT_MAX;

int IMU_xAccel = INT_MAX;
int IMU_yAccel = INT_MAX;
int IMU_zAccel = INT_MAX;

float LC_scaleValue = -34200; // set this default
long LC_offsetValue = 0;
float LC_Force = 9999999;
string message = "";
int systemErrorState = 0; // 0 = no error, 1 = error
int counter = 0;

float ADXL1_x, ADXL1_y, ADXL1_z;
float ADXL2_x, ADXL2_y, ADXL2_z;
int AccelMinX, AccelMinY, AccelMinZ;
int AccelMaxX, AccelMaxY, AccelMaxZ;

float gainX = 1;
float gainY = 1;
float gainZ = 1;

float offsetX = 0;
float offsetY = 0;
float offsetZ = 0;

int rawX, rawY, rawZ; // init variables hold results

TwoWire I2Cone = TwoWire(0); // GPS I2C bus

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
      // systemErrorState = 1;
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
    Serial.println("Set Nav Frequency Successful");
  }
  else
  {
    Serial.println("ERROR Set Nav Frequency Failed");
    systemErrorState = 1;
  }

  myGNSS.setESFAutoAlignment(true); // Enable Automatic IMU-mount Alignment

  if (myGNSS.getEsfInfo())
  {
    Serial.print(F("Fusion Mode: "));
    Serial.print(myGNSS.packetUBXESFSTATUS->data.fusionMode);
    if (myGNSS.packetUBXESFSTATUS->data.fusionMode == 0)
      Serial.println(F("  Sensor is initializing..."));
    else if (myGNSS.packetUBXESFSTATUS->data.fusionMode == 1)
      Serial.println(F("  Sensor is calibrated!"));
    else if (myGNSS.packetUBXESFSTATUS->data.fusionMode == 2)
      Serial.println(F("  Sensor fusion is suspended!"));
    else if (myGNSS.packetUBXESFSTATUS->data.fusionMode == 3)
      Serial.println(F("  Sensor fusion is disabled!"));
  }
  else
  {
    Serial.println("ERROR fusion mode not set up");
  }

  adxl_1.powerOn(ADXL_SDA, ADXL_SCL);
  adxl_1.setRangeSetting(ADXL_RANGE);
  
  adxl_2.powerOn(ADXL_SDA, ADXL_SCL);
  adxl_2.setRangeSetting(ADXL_RANGE);

  adxl_1.readAccel(&rawX, &rawY, &rawZ); // initialise the ranges to a real value
  AccelMaxX = rawX;
  AccelMinX = rawX;
  AccelMaxY = rawY;
  AccelMinY = rawY;
  AccelMaxZ = rawZ;
  AccelMinZ = rawZ;

  if (EEPROM.get(8, gainX) && EEPROM.get(12, gainY) && EEPROM.get(16, gainZ))
  {
    Serial.print("ADXL Gain values loaded from EEPROM: ");
    Serial.print(gainX);
    Serial.print(" ");
    Serial.print(gainY);
    Serial.print(" ");
    Serial.println(gainZ);
  }
  else
  {
    Serial.println("ERROR: ADXL Gain values not found in EEPROM");
    systemErrorState = 1;
  }

  if (EEPROM.get(20, offsetX) && EEPROM.get(24, offsetY) && EEPROM.get(28, offsetZ))
  {
    Serial.print("ADXL Offset values loaded from EEPROM: ");
    Serial.print(offsetX);
    Serial.print(" ");
    Serial.print(offsetY);
    Serial.print(" ");
    Serial.println(offsetZ);
  }
  else
  {
    Serial.println("ERROR: ADXL Offset values not found in EEPROM");
    systemErrorState = 1;
  }

  if(ELM.initialize()== false) {
    Serial.println("ERROR: ELM327 not initialized");
    systemErrorState = 1;
  }
  else {
    Serial.println("ELM327 initialized");
  }

  if (!systemErrorState)
    Serial.println("Setup completed with no errors............................................");
  else
    Serial.println("ERROR Setup completed with errors............................................");
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
      scale.tare(); // Reset the scale to 0
      Serial.print("Scale zeroed, offset value: ");
      LC_offsetValue = scale.get_offset();
      Serial.println(LC_offsetValue);
      EEPROM.put(4, LC_offsetValue);
      EEPROM.commit();
    }

    if (str.startsWith("<LC10kg>")) // 10kg calibration
    {
      scale.calibrate_scale(980, 5);
      LC_scaleValue = scale.get_scale();
      Serial.print("Calibration done at 10kg, scale value: ");
      Serial.println(LC_scaleValue);
      EEPROM.put(0, LC_scaleValue);
      EEPROM.commit();
    }

    if (str.startsWith("<resetESP>")) // 10kg calibration
    {
      Serial.print("ESP Will reset");
      // reset the esp32
      ESP.restart();
    }

    if (str.startsWith("<CALGYS>"))
    {

      adxl_1.readAccel(&rawX, &rawY, &rawZ);

      if (rawX < AccelMinX)
        AccelMinX = rawX;
      if (rawX > AccelMaxX)
        AccelMaxX = rawX;

      if (rawY < AccelMinY)
        AccelMinY = rawY;
      if (rawY > AccelMaxY)
        AccelMaxY = rawY;

      if (rawZ < AccelMinZ)
        AccelMinZ = rawZ;
      if (rawZ > AccelMaxZ)
        AccelMaxZ = rawZ;

      Serial.print("Accel Minimums: ");
      Serial.print(AccelMinX);
      Serial.print("  ");
      Serial.print(AccelMinY);
      Serial.print("  ");
      Serial.print(AccelMinZ);
      Serial.println();

      Serial.print("Accel Maximums: ");
      Serial.print(AccelMaxX);
      Serial.print("  ");
      Serial.print(AccelMaxY);
      Serial.print("  ");
      Serial.print(AccelMaxZ);
      Serial.println();
    }

    if (str.startsWith("<SAVEGYS>"))
    {
      // CorrectedValue = (((RawValue – RawLow) * ReferenceRange) / RawRange) + ReferenceLow
      gainX = 0.5 * (AccelMaxX - AccelMinX);
      EEPROM.put(8, gainX);
      gainY = 0.5 * (AccelMaxY - AccelMinY);
      EEPROM.put(12, gainY);
      gainZ = 0.5 * (AccelMaxZ - AccelMinZ);
      EEPROM.put(16, gainZ);

      offsetX = 0.5 * (AccelMaxX + AccelMinX);
      EEPROM.put(20, offsetX);
      offsetY = 0.5 * (AccelMaxY + AccelMinY);
      EEPROM.put(24, offsetY);
      offsetZ = 0.5 * (AccelMaxZ + AccelMinZ);
      EEPROM.put(28, offsetZ);

      if (EEPROM.commit())
      {
        Serial.println("EEPROM ADXL write successful");
      }
      else
      {
        Serial.println("ERROR EEPROM ADXL write failed");
      }

      Serial.print("Gain X: ");
      Serial.print(gainX);
      Serial.print(" Gain Y: ");
      Serial.print(gainY);
      Serial.print(" Gain Z: ");
      Serial.println(gainZ);

      Serial.print("Offset X: ");
      Serial.print(offsetX);
      Serial.print(" Offset Y: ");
      Serial.print(offsetY);
      Serial.print(" Offset Z: ");
      Serial.println(offsetZ);
    }
  }

  long time = millis();
  long GPS_lat = myGNSS.getLatitude();
  long GPS_long = myGNSS.getLongitude();
  long GPS_groundSpeed_mms = myGNSS.getGroundSpeed();
  float GPS_groundSpeed = GPS_groundSpeed_mms * 0.001 * 3.6;
  long GPS_heading_105 = myGNSS.getHeading();
  float GPS_heading = GPS_heading_105 * 0.000001; // degrees
  int GPS_Seconds = myGNSS.getSecond();
  int GPS_Minutes = myGNSS.getMinute();
  int GPS_Hours = myGNSS.getHour();
  int GPS_Day = myGNSS.getDay();
  int GPS_Month = myGNSS.getMonth();

  if (scale.is_ready())
  { // only proceed if HX711 is ready to read
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

  adxl_1.readAccel(&rawX, &rawY, &rawZ);

  ADXL1_x = (rawX - offsetX) * 9.81 / gainX;
  ADXL1_y = (rawY - offsetY) * 9.81 / gainY;
  ADXL1_z = (rawZ - offsetZ) * 9.81 / gainZ;

  adxl_2.readAccel(&rawX, &rawY, &rawZ);

  ADXL2_x = (rawX - offsetX) * 9.81 / gainX;
  ADXL2_y = (rawY - offsetY) * 9.81 / gainY;
  ADXL2_z = (rawZ - offsetZ) * 9.81 / gainZ;

  String ThrottlePos = ELM.send("01 11");
 
  if (systemErrorState == 1)
  {
    // Serial.println("ERROR system error");
    // vTaskDelay(10000 / portTICK_PERIOD_MS);
    return;
  }
  else
  {
    counter += 1;

    if (counter > 40)
    {
      Serial.println("HEADtime,GPS_groundSpeed,GPS_lat,GPS_long,GPS_heading,GPS_Seconds,GPS_Minutes,GPS_Hours,GPS_Day,GPS_Month,LC_Force,IMU_roll,IMU_pitch,IMU_yaw,IMU_xAccel,IMU_yAccel,IMU_zAccel,ADXL1_x,ADXL1_y,ADXL1_z,ADXL2_x,ADXL2_y,ADXL2_z,ThrottlePos");
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
    Serial.print(IMU_zAccel);
    Serial.print(",");
    Serial.print(ADXL1_x);
    Serial.print(",");
    Serial.print(ADXL1_y);
    Serial.print(",");
    Serial.print(ADXL1_z);
    Serial.print(",");
    Serial.print(ADXL2_x);
    Serial.print(",");
    Serial.print(ADXL2_y);
    Serial.print(",");
    Serial.print(ADXL2_z);
    Serial.print(",");
    Serial.println(ThrottlePos);
  }
}
