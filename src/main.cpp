#include <Wire.h> //Needed for I2C to GPS
#include <EEPROM.h>
#include "SparkFun_u-blox_GNSS_Arduino_Library.h" //Click here to get the library: http://librarymanager/All#SparkFun_u-blox_GNSS
#include "HX711.h"
#include <SparkFun_ADXL345.h>
#include <Arduino.h>
#include "ELMo.h"
#include <main.h>

#include "BluetoothSerial.h"
#include "ELMduino.h"

#include <iomanip>
#include <iostream>

BluetoothSerial SerialBT;
#define ELM_PORT SerialBT
#define DEBUG_PORT Serial

ELM327 myELM327;

#define LC_DOUT 4  // LOADCELL
#define LC_CLK 2   // LOADCELL
#define GPS_SDA 22 // GPS
#define GPS_SCL 23 // GPS
#define GPS_NAVFREQ 20
#define ADXL_SDA 25   // ADXL345
#define ADXL_SCL 26   // ADXL345
#define ADXL_RANGE 16 // 2,4,8,16

#define SECONDADXL false

TwoWire I2Cone = TwoWire(0); // GPS I2C bus
TwoWire I2Ctwo = TwoWire(1); // ADXL I2C bus

HX711 scale;
SFE_UBLOX_GNSS myGNSS;
ADXL345 adxl_1 = ADXL345(0x53, I2Ctwo);
#if SECONDADXL
ADXL345 adxl_2 = ADXL345(0x1D, I2Ctwo);
#endif
ICM_20948_I2C ICM; // I2C 0x68

long timeNow, timeAtBoot = 0;
long GPS_lat, GPS_long = 9999;
float GPS_groundSpeed = 9999;
float GPS_heading = 9999; // degrees
int GPS_Seconds, GPS_Minutes, GPS_Hours, GPS_Day, GPS_Month, GPS_Sats, GPS_Precision = 9999;

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

float ADXL1_x, ADXL1_y, ADXL1_z = 9999;
float ADXL2_x, ADXL2_y, ADXL2_z = 9999;
int AccelMinX, AccelMinY, AccelMinZ;
int AccelMaxX, AccelMaxY, AccelMaxZ;

float ICM_aX, ICM_aY, ICM_aZ = 9999;
float ICM_gX, ICM_gY, ICM_gZ = 9999;
float ICM_mX, ICM_mY, ICM_mZ = 9999;

float gainX = 1;
float gainY = 1;
float gainZ = 1;

float offsetX = 0;
float offsetY = 0;
float offsetZ = 0;

int rawX, rawY, rawZ; // init variables hold results

float throttlePos = 999;
float rpm = 999;

bool useLC = true, useGPS = true, useGYS = true;
bool useOBD= false, useICM = true;

void setup()
{
  Serial.begin(115200);
  Serial.println("Relativity DAQ v1.0.0");
  Serial.println("Setup started............................................");

  timeAtBoot = millis();
  EEPROM.begin(512); // Initialize EEPROM with a size of 512 bytes
  

  if (!setupLoadCell())
  {
    systemErrorState = 1;
  }

  if (!setupGPS())
  {
    if (!setupGPS())
    {
      systemErrorState = 1;
    }
  }

  if (!setupGYS())
  {
    systemErrorState = 1;
  }

  if (!setupOBD())
  {
    systemErrorState = 1;
  }

  if (!setupICM())
  {
    systemErrorState = 1;
  }

  if (!systemErrorState)
    Serial.println("Setup completed with no errors............................................");
  else
    Serial.println("ERROR Setup completed with errors............................................");
}

void loop()
{
  config();

  if (systemErrorState == 1)
  {
    // Serial.println("ERROR system error");
    // vTaskDelay(10000 / portTICK_PERIOD_MS);
    return;
  }
  else
  {
    logGPS();
    logLoadCell();
    logGYS();
    logOBD();
    logICM();

    counter += 1;

    if (counter > 40)
    {
      Serial.println("HEADtime,GPS_groundSpeed,GPS_lat,GPS_long,GPS_heading,GPS_Seconds,GPS_Minutes,GPS_Hours,GPS_Day,GPS_Month,LC_Force,ADXL1_x,ADXL1_y,ADXL1_z,ADXL2_x,ADXL2_y,ADXL2_z,ThrottlePos,rpm,ICM_ax,ICM_ay,ICM_az,ICM_gx,ICM_gy,ICM_gz,ICM_mx,ICM_my,ICM_mz,GPS_Sats,GPS_Precision");
      counter = 0;
    }

    timeNow = millis() - timeAtBoot;

    Serial.print("DATA");
    Serial.print(timeNow); // 0
    Serial.print(",");
    Serial.print(GPS_groundSpeed);
    Serial.print(",");
    Serial.print(GPS_lat); // 2
    Serial.print(",");
    Serial.print(GPS_long);
    Serial.print(",");
    Serial.print(GPS_heading); // 4
    Serial.print(",");
    Serial.print(GPS_Seconds);
    Serial.print(",");
    Serial.print(GPS_Minutes); // 6
    Serial.print(",");
    Serial.print(GPS_Hours);
    Serial.print(",");
    Serial.print(GPS_Day); // 8
    Serial.print(",");
    Serial.print(GPS_Month);
    Serial.print(",");
    Serial.print(LC_Force); // 10
    Serial.print(",");
    Serial.print(ADXL1_x);
    Serial.print(",");
    Serial.print(ADXL1_y); // 12
    Serial.print(",");
    Serial.print(ADXL1_z);
    Serial.print(",");
    Serial.print(ADXL2_x); // 14
    Serial.print(",");
    Serial.print(ADXL2_y);
    Serial.print(",");
    Serial.print(ADXL2_z); // 16
    Serial.print(",");
    Serial.print(throttlePos);
    Serial.print(",");
    Serial.print(rpm); // 18
    Serial.print(",");
    Serial.print(ICM_aX);
    Serial.print(",");
    Serial.print(ICM_aY); // 20
    Serial.print(",");
    Serial.print(ICM_aZ);
    Serial.print(",");
    Serial.print(ICM_gX); // 22
    Serial.print(",");
    Serial.print(ICM_gY);
    Serial.print(",");
    Serial.print(ICM_gZ); // 24
    Serial.print(",");
    Serial.print(ICM_mX);
    Serial.print(",");
    Serial.print(ICM_mY); // 26
    Serial.print(",");
    Serial.print(ICM_mZ);
    Serial.print(",");
    Serial.print(GPS_Sats); // 28
    Serial.print(",");
    Serial.print(GPS_Precision); // 30
    Serial.println();
  }
}

bool setupLoadCell()
{
  if(useLC) {
  Serial.println("Begin LC setup");
  if (EEPROM.get(0, LC_scaleValue))
  {
    Serial.print("LC scale factor loaded from EEPROM: ");
    Serial.println(LC_scaleValue);
    if (LC_scaleValue < 2000 || LC_scaleValue > 4000)
    {
      Serial.println("ERROR: LC Calibration factor out of range");
      return false;
    }
  }
  else
  {
    Serial.print("ERROR: LC Calibration factor not found in EEPROM ");
    Serial.println(LC_scaleValue);
    return false;
  }

  if (EEPROM.get(4, LC_offsetValue))
  {
    Serial.print("LC Tare value loaded from EEPROM: ");
    Serial.println(LC_offsetValue);
  }
  else
  {
    Serial.print("ERROR: LC Tare value not found in EEPROM");
    return false;
  }

  scale.begin(LC_DOUT, LC_CLK);
  scale.set_offset(LC_offsetValue);
  scale.set_scale(LC_scaleValue);
  scale.set_raw_mode();

  Serial.println("LC setup completed OK");
  }
  return true;
}

bool setupGPS()
{
  if(useGPS) {
  Serial.println("Begin GPS setup");
  I2Cone.begin(GPS_SDA, GPS_SCL, 400000); // SDA, SCL

  if (myGNSS.begin(I2Cone) == false)
  {
    Serial.println(F("ERROR u-blox GNSS module not detected at I2C address. Please check wiring."));
    return false;
  }

  myGNSS.setI2COutput(COM_TYPE_UBX); // Set the I2C port to output UBX only (turn off NMEA noise)

  if (myGNSS.setNavigationFrequency(GPS_NAVFREQ))
  {
    Serial.println("Set Nav Frequency Successful");
  }
  else
  {
    Serial.println("ERROR Set Nav Frequency Failed");
    return false;
  }
  Serial.println("GPS setup completed OK");
  }
  
  return true;
}

bool setupGYS()
{
  if(useGYS) {
  // initializeADXL345(ADXL_SDA, ADXL_SCL);
Serial.println("Begin GYS setup");
  I2Ctwo.begin(ADXL_SDA, ADXL_SCL, 400000); // SDA, SCL

  adxl_1.powerOn();
  adxl_1.setRangeSetting(ADXL_RANGE);

#if SECONDADXL
  adxl_2.powerOn();
  adxl_2.setRangeSetting(ADXL_RANGE);
#endif

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
    return false;
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
    return false;
  }
  Serial.println("GYS setup completed OK");
  }
  
  return true;
}

bool setupOBD()
{
  if(useOBD) {
    Serial.println("Begin OBD setup");
  // establish BT connection
  SerialBT.begin("RelativityDAQ", true);

  Serial.println("Trying to connect to OBD via BT...");
  if (!SerialBT.connect("OBDII"))
  {
    Serial.println("ERROR: Couldn't connect to Bluetooth");
    return false;
  }
  else
  {
    Serial.println("Connected to BT OK");
  }
  // Connect to ELM chip
  Serial.println("Trying to connect to ELM327...");
  if (!myELM327.begin(SerialBT, false, 100))
  {
    Serial.println("ERROR: Couldn't connect to ELM327");
    return false;
  }
  else
  {
    Serial.println("Connected to ELM327 OK");
  }
  uint32_t pidsSupported= myELM327.supportedPIDs_1_20();

  if (myELM327.nb_rx_state == ELM_SUCCESS)
  {
    Serial.print("PIDs 1-20 supported: ");
    Serial.println(pidsSupported, BIN);
  }
  Serial.println("OBD setup completed OK");
  }
  
  return true;
}

bool setupICM()
{
  if(useICM) {
  Serial.println("Begin ICM setup");
  ICM.begin(I2Ctwo, 1);

  if (ICM.status != ICM_20948_Stat_Ok)
  {
    Serial.println("ICM sensor not set up, Trying again...");
    ICM.begin(I2Ctwo, 1);
  }
  if (ICM.status != ICM_20948_Stat_Ok)
  {
    Serial.println("ERROR ICM sensor not set up");
    return false;
  }

  ICM.enableDebugging();
  ICM.sleep(false);
  ICM.lowPower(false);
  ICM.setSampleMode((ICM_20948_Internal_Acc | ICM_20948_Internal_Gyr), ICM_20948_Sample_Mode_Continuous);

  ICM_20948_fss_t myFSS;
  myFSS.a = gpm2; // 2g range accel
  myFSS.a = gpm2; // 250dps range gyro
  ICM.setFullScale((ICM_20948_Internal_Acc | ICM_20948_Internal_Gyr), myFSS);

  // Set up Digital Low-Pass Filter configuration
  ICM_20948_dlpcfg_t myDLPcfg;
  myDLPcfg.a = acc_d473bw_n499bw;
  myDLPcfg.g = gyr_d361bw4_n376bw5;
  ICM.setDLPFcfg((ICM_20948_Internal_Acc | ICM_20948_Internal_Gyr), myDLPcfg);

  // Choose whether or not to start the magnetometer
  ICM.startupMagnetometer();
  if (ICM.status != ICM_20948_Stat_Ok)
  {
    Serial.print(F("ERROR startupMagnetometer returned: "));
    Serial.println(ICM.statusString());
    return false;
  }

  Serial.print(F("ICM setup complete, ICM reporting: "));
  Serial.println(ICM.statusString());
  Serial.println("ICM setup completed OK");
  }
  return true;
}

void config()
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
      scale.calibrate_scale(98, 5);
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
}

void logLoadCell()
{
  if(useLC) {
  if (scale.is_ready())
  { // only proceed if HX711 is ready to read
    LC_Force = scale.get_units();
  }
}
}

void logGYS()
{
  if(useGYS) {
  adxl_1.readAccel(&rawX, &rawY, &rawZ);

  ADXL1_x = (rawX - offsetX) * 9.81 / gainX;
  ADXL1_y = (rawY - offsetY) * 9.81 / gainY;
  ADXL1_z = (rawZ - offsetZ) * 9.81 / gainZ;

#if SECONDADXL
  adxl_2.readAccel(&rawX, &rawY, &rawZ);

  ADXL2_x = (rawX - offsetX) * 9.81 / gainX;
  ADXL2_y = (rawY - offsetY) * 9.81 / gainY;
  ADXL2_z = (rawZ - offsetZ) * 9.81 / gainZ;
#endif
  }
}

void logOBD()
{
  if(useOBD) {
  float throttlePosTemp = myELM327.throttle();

  if (myELM327.nb_rx_state == ELM_SUCCESS)
  {
    throttlePos = throttlePosTemp;
  }

  float rmpTemp = myELM327.rpm();
  if (myELM327.nb_rx_state == ELM_SUCCESS)
  {
    rpm = rmpTemp;
  }
  }
}

void logGPS()
{
  if(useGPS) {
  GPS_lat = myGNSS.getLatitude();
  GPS_long = myGNSS.getLongitude();
  int GPS_groundSpeed_mms = myGNSS.getGroundSpeed();
  GPS_groundSpeed = GPS_groundSpeed_mms * 0.001 * 3.6;
  int GPS_heading_105 = myGNSS.getHeading();
  GPS_heading = GPS_heading_105 * 0.000001; // degrees
  GPS_Seconds = myGNSS.getSecond();
  GPS_Minutes = myGNSS.getMinute();
  GPS_Hours = myGNSS.getHour();
  GPS_Day = myGNSS.getDay();
  GPS_Month = myGNSS.getMonth();
  GPS_Sats = myGNSS.getSIV();
  //GPS_Precision = myGNSS.getHorizontalAccuracy();
  }
}

void logICM()
{
  if(useICM) {
  if (ICM.dataReady())
  {
    ICM.getAGMT(); // The values are only updated when you call 'getAGMT'

    ICM_aX = round(ICM.accX() * 0.001 * 10) / 10;
    ICM_aY = round(ICM.accY() * 0.001 * 10) / 10;
    ICM_aZ = round(ICM.accZ() * 0.001 * 10) / 10;

    ICM_gX = ICM.gyrX();
    ICM_gY = ICM.gyrY();
    ICM_gZ = ICM.gyrZ();
    ICM_mX = ICM.magX();
    ICM_mY = ICM.magY();
    ICM_mZ = ICM.magZ();
  }
  }
}
