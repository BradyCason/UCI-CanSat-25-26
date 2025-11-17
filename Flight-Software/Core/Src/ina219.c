#include "ina219.h"

#define INA219_REG_CONFIG      0x00
#define INA219_REG_CALIB       0x05
#define INA219_REG_BUS_VOLTAGE 0x02
#ifndef INA219_ADDRESS
#define INA219_ADDRESS (0x40 << 1)
#endif

static HAL_StatusTypeDef wr16(I2C_HandleTypeDef *hi2c, uint8_t reg, uint16_t val){
  uint8_t b[2] = { (uint8_t)(val>>8), (uint8_t)val };
  return HAL_I2C_Mem_Write(hi2c, INA219_ADDRESS, reg, I2C_MEMADD_SIZE_8BIT, b, 2, 100);
}
static HAL_StatusTypeDef rd16(I2C_HandleTypeDef *hi2c, uint8_t reg, uint16_t *out){
  uint8_t b[2];
  HAL_StatusTypeDef st = HAL_I2C_Mem_Read(hi2c, INA219_ADDRESS, reg, I2C_MEMADD_SIZE_8BIT, b, 2, 100);
  if (st==HAL_OK) *out = ((uint16_t)b[0]<<8)|b[1];
  return st;
}

bool ina219_init(I2C_HandleTypeDef *hi2c){
  if (wr16(hi2c, INA219_REG_CONFIG, 0x019F) != HAL_OK) return false; // generic
  (void)wr16(hi2c, INA219_REG_CALIB, 0x2000);                        // placeholder
  return true;
}
bool ina219_read_bus_voltage(I2C_HandleTypeDef *hi2c, float *volts){
  uint16_t raw=0;
  if (rd16(hi2c, INA219_REG_BUS_VOLTAGE, &raw) != HAL_OK) return false;
  raw >>= 3;
  *volts = raw * 0.004f; // 4mV/LSB
  return true;
}
