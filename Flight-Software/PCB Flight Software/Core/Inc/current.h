#pragma once
#include "stm32f4xx_hal.h"
#include <stdbool.h>
#include "telemetry.h"

void init_current(I2C_HandleTypeDef *hi2c);
void read_current(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry);
