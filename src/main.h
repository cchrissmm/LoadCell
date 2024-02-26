#ifndef MAIN_H_
#define MAIN_H_

#include <Arduino.h>
#include <string>
using std::string;
using std::to_string;
#include "ICM_20948.h"

void printFormattedFloat(float val, uint8_t leading, uint8_t decimals);
void printScaledAGMT(ICM_20948_I2C *sensor);

bool setupOBD();
bool setupGPS();
bool setupGYS();
bool setupLoadCell();
bool setupICM();
void calGYS();

void logOBD();
void logGPS();
void logGYS();
void logLoadCell();
void logICM();


#endif /* MAIN_H_ */