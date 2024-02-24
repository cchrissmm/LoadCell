# Relativity Engineering Data Logger

# ADXL345 Input
This is connected by I2C, two sensors can be connected to the same bus.
The pinouts need to be

| Pin | State Sensor 1| State Sensor 2 | Wire Colour| Comment|
| --------------- | --------------- | ------------ |------------|--------------------|
|Address |0x53|0x1d|||
| VCC | 3V3 | 3V3 |RED||
| GND | GND | GND |BLK||
|CS|3V3|3V3| Internal bridge | To select I2C, dont leave floating|
|SDA|||YEL||
|SCL|||WHT||
|SDO|3V3|GND|Internal Bridge|To switch address|

# ICM20948 Input
This is connected by I2C, two sensors can be connected to the same bus.
The pinouts need to be

| Pin Sensor| Pin ESP32 | Wire Colour| Comment|
| --------------- | --------------- | ------------ |------------|
|Address |0x68|||
| VIN | 3V3 |RED|
| GND | GND |BLK|
|DA|SDA|YEL|
|CL|SCL|WHT|
