#pragma once
#include "main.h"
#include <stdbool.h>

bool ina219_init(I2C_HandleTypeDef *hi2c);
bool ina219_read_bus_voltage(I2C_HandleTypeDef *hi2c, float *volts);
