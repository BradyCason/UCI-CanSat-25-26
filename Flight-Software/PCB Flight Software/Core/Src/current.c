#include "current.h"

#define INA219_ADDRESS (0x40 << 1)
#define INA219_REG_CONFIG       0x00
#define INA219_REG_SHUNT_VOLT   0x01
#define INA219_REG_BUS_VOLT     0x02
#define INA219_REG_POWER        0x03
#define INA219_REG_CURRENT      0x04
#define INA219_REG_CALIBRATION  0x05

void init_current(I2C_HandleTypeDef *hi2c)
{
	// OLD CODE --------------------------------------------------------------------------
	// This is writing to the CALIBRATION register (0x05), not the CONFIG register (0x00)!
//	uint8_t ina_calib[2] = {0x20, 0x00};  // Example calibration value
//	result2 = HAL_I2C_Mem_Write(&hi2c1, INA219_ADDRESS, 0x05, 1, ina_calib, 2, 1000);
//
//	// Now write to the CONFIG register (0x00)
//	uint8_t ina_config[2] = {0x01, 0x9F};  // Example: 32V, 2A, 12-bit ADCs
//	HAL_I2C_Mem_Write(&hi2c1, INA219_ADDRESS, 0x00, 1, ina_config, 2, 1000);

	// NEW CODE --------------------------------------------------------------------------
	// Calibration for 0.1Ω shunt, 2A max
	uint16_t calib = 0x1A36;  // 6710 decimal
	uint8_t calib_buf[2] = { calib >> 8, calib & 0xFF };

	HAL_I2C_Mem_Write(hi2c, INA219_ADDRESS,
					  INA219_REG_CALIBRATION,
					  I2C_MEMADD_SIZE_8BIT,
					  calib_buf, 2, HAL_MAX_DELAY);

	// Config: 32V range, ±320mV shunt, 12-bit ADCs, continuous
	uint16_t config = 0x019F;
	uint8_t config_buf[2] = { config >> 8, config & 0xFF };

	HAL_I2C_Mem_Write(hi2c, INA219_ADDRESS,
					  INA219_REG_CONFIG,
					  I2C_MEMADD_SIZE_8BIT,
					  config_buf, 2, HAL_MAX_DELAY);
}

void read_current(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry) {
	/* INA219 (CURRENT/VOLTAGE) */

	// OLD CODE ----------------------------------------------------------------------------
//	uint8_t reg = 0x02;  // Bus voltage register
//	uint8_t ina_buf[2];
//
//	ina_ret = HAL_I2C_IsDeviceReady(&hi2c1, INA219_ADDRESS, 3, 5);
//	if (ina_ret == HAL_OK) {
//		// Write the register address
//		ina_ret = HAL_I2C_Master_Transmit(&hi2c1, INA219_ADDRESS, &reg, 1, 100);
//		if (ina_ret == HAL_OK) {
//			// Read 2 bytes from that register
//			ina_ret = HAL_I2C_Master_Receive(&hi2c1, INA219_ADDRESS, ina_buf, 2, 10);
//			if (ina_ret == HAL_OK) {
//				uint16_t raw_bus_voltage = (ina_buf[0] << 8) | ina_buf[1];
//				raw_bus_voltage >>= 3;  // per datasheet, remove unused bits
//
//				float bus_voltage = raw_bus_voltage * 0.004;  // each bit = 4mV
//				telemetry->voltage = bus_voltage;
//
//				// For debug:
//				// printf("Bus voltage: %.3f V\n", voltage);
//			}
//		}
//	}

	// NEW CODE ----------------------------------------------------------------------------
	uint8_t buf[2];

	// ---------------- Bus Voltage ----------------
	if (HAL_I2C_Mem_Read(hi2c, INA219_ADDRESS,
						 INA219_REG_BUS_VOLT,
						 I2C_MEMADD_SIZE_8BIT,
						 buf, 2, HAL_MAX_DELAY) == HAL_OK)
	{
		uint16_t raw_bus = (buf[0] << 8) | buf[1];
		raw_bus >>= 3; // remove CNVR + OVF bits

		telemetry->voltage = raw_bus * 0.004f; // 4 mV per bit
	}

	// ---------------- Current ----------------
	if (HAL_I2C_Mem_Read(hi2c, INA219_ADDRESS,
						 INA219_REG_CURRENT,
						 I2C_MEMADD_SIZE_8BIT,
						 buf, 2, HAL_MAX_DELAY) == HAL_OK)
	{
		int16_t raw_current = (int16_t)((buf[0] << 8) | buf[1]);

		// Current LSB = 61 µA
		telemetry->current = raw_current * 0.000061f; // Amps
	}
}
