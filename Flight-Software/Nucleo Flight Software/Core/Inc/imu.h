#pragma once
#include <stdbool.h>
#include "stm32f4xx_hal.h"
#include <stdint.h>
#include "telemetry.h"

#define BNO055_ADDR        (0x28 << 1) // 8-bit HAL address
#define BNO055_CHIP_ID     0xA0

// Registers
#define BNO055_CHIP_ID_ADDR       0x00
#define BNO055_OPR_MODE_ADDR      0x3D
#define BNO055_PWR_MODE_ADDR      0x3E
#define BNO055_UNIT_SEL_ADDR      0x3B
#define BNO055_TEMP_SOURCE_ADDR   0x40

#define BNO055_ACC_DATA_X_LSB     0x08
#define BNO055_GYR_DATA_X_LSB     0x14
#define BNO055_LIA_DATA_X_LSB     0x28
#define BNO055_MAG_DATA_X_LSB     0x0E

// Operation modes
#define BNO055_OPR_MODE_CONFIG    0x00
#define BNO055_OPR_MODE_NDOF      0x0C

// Power modes
#define BNO055_PWR_MODE_NORMAL    0x00

// Unit selection: degrees, m/s², etc.
#define BNO055_UNIT_SEL_DEFAULT   0x00

HAL_StatusTypeDef init_imu(I2C_HandleTypeDef *hi2c);
HAL_StatusTypeDef read_imu(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry);
