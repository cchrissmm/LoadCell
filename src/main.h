#ifndef MAIN_H_
#define MAIN_H_

#include <Arduino.h>
#include <string>
using std::string;
using std::to_string;

bool setupOBD();
bool setupGPS();
bool setupGYS();
bool setupLoadCell();
bool setupICM();
void calGYS();

#endif /* MAIN_H_ */