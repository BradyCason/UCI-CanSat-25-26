#pragma once

#include "stm32f4xx_hal.h"
#include <stdint.h>
#include <math.h>
#include "telemetry.h"

#define BMP280_ADDR         (0x77 << 1)  // STM32 HAL 8-bit address
#define BMP280_REG_ID       0xD0
#define BMP280_REG_RESET    0xE0
#define BMP280_REG_CTRL_MEAS 0xF4
#define BMP280_REG_CONFIG   0xF5
#define BMP280_REG_PRESS_MSB 0xF7
#define BMP280_REG_CALIB    0x88

typedef struct {
    uint16_t dig_T1;
    int16_t  dig_T2;
    int16_t  dig_T3;

    uint16_t dig_P1;
    int16_t  dig_P2;
    int16_t  dig_P3;
    int16_t  dig_P4;
    int16_t  dig_P5;
    int16_t  dig_P6;
    int16_t  dig_P7;
    int16_t  dig_P8;
    int16_t  dig_P9;

    int32_t t_fine;
} BMP280_CalibData;

float calculate_altitude(Telemetry_t *telemetry);
HAL_StatusTypeDef init_baro(I2C_HandleTypeDef *hi2c);
void read_baro(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry);
