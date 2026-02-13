#pragma once
#include <stdbool.h>
#include <stdint.h>
#include "stm32f4xx_hal.h"
#include "telemetry.h"

void init_gps(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry);
bool read_gps(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry);
void flush_gps(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry);
