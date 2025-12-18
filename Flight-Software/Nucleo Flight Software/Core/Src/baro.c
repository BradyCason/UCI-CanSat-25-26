#include "baro.h"

static BMP280_CalibData bmp280_calib;
static int32_t t_fine;

float calculate_altitude(Telemetry_t *telemetry) {
	return 44330.77 * (1 - powf(telemetry->pressure / 101.326, 0.1902632)) + telemetry->altitude_offset;
}

HAL_StatusTypeDef BMP280_WriteReg(I2C_HandleTypeDef *hi2c, uint8_t reg, uint8_t value)
{
    return HAL_I2C_Mem_Write(hi2c, BMP280_ADDR, reg, I2C_MEMADD_SIZE_8BIT, &value, 1, HAL_MAX_DELAY);
}

HAL_StatusTypeDef BMP280_ReadRegs(I2C_HandleTypeDef *hi2c, uint8_t reg, uint8_t *buffer, uint8_t length)
{
    return HAL_I2C_Mem_Read(hi2c, BMP280_ADDR, reg, I2C_MEMADD_SIZE_8BIT, buffer, length, HAL_MAX_DELAY);
}

HAL_StatusTypeDef init_baro(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry)
{
    uint8_t id;
    if (BMP280_ReadRegs(hi2c, BMP280_REG_ID, &id, 1) != HAL_OK) return HAL_ERROR;
    if (id != BMP280_ID_VALUE) return HAL_ERROR;

    // Reset sensor
    BMP280_WriteReg(hi2c, BMP280_REG_RESET, BMP280_RESET_VALUE);
    HAL_Delay(100);

    // Read calibration
    if (read_baro(hi2c, telemetry) != HAL_OK) return HAL_ERROR;

    // Normal mode, temp & pressure oversampling x1
    BMP280_WriteReg(hi2c, BMP280_REG_CTRL_MEAS, (1 << 5) | (1 << 2) | 3);

    // Standby 500ms, filter off
    BMP280_WriteReg(hi2c, BMP280_REG_CONFIG, (5 << 5));

    return HAL_OK;
}

HAL_StatusTypeDef read_baro(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry)
{
    uint8_t buf[6];
    if (BMP280_ReadRegs(hi2c, BMP280_REG_PRESS_MSB, buf, 6) != HAL_OK) return HAL_ERROR;

    int32_t adc_p = ((int32_t)buf[0] << 12) | ((int32_t)buf[1] << 4) | (buf[2] >> 4);
    int32_t adc_t = ((int32_t)buf[3] << 12) | ((int32_t)buf[4] << 4) | (buf[5] >> 4);

    // Temperature compensation
    int32_t var1 = ((((adc_t >> 3) - ((int32_t)bmp280_calib.dig_T1 << 1))) * ((int32_t)bmp280_calib.dig_T2)) >> 11;
    int32_t var2 = (((((adc_t >> 4) - ((int32_t)bmp280_calib.dig_T1)) *
                     ((adc_t >> 4) - ((int32_t)bmp280_calib.dig_T1))) >> 12) *
                     ((int32_t)bmp280_calib.dig_T3)) >> 14;
    t_fine = var1 + var2;
    telemetry->temperature = (t_fine * 5 + 128) >> 8;
    telemetry->temperature /= 100.0f; // °C

    // Pressure compensation
    int64_t var1_p, var2_p, p;
    var1_p = ((int64_t)t_fine) - 128000;
    var2_p = var1_p * var1_p * (int64_t)bmp280_calib.dig_P6;
    var2_p += ((var1_p * (int64_t)bmp280_calib.dig_P5) << 17);
    var2_p += ((int64_t)bmp280_calib.dig_P4 << 35);
    var1_p = ((var1_p * var1_p * (int64_t)bmp280_calib.dig_P3) >> 8) + ((var1_p * (int64_t)bmp280_calib.dig_P2) << 12);
    var1_p = (((((int64_t)1) << 47) + var1_p) * ((int64_t)bmp280_calib.dig_P1)) >> 33;

    if (var1_p == 0) return HAL_ERROR; // avoid division by zero

    p = 1048576 - adc_p;
    p = (((p << 31) - var2_p) * 3125) / var1_p;
    var1_p = (((int64_t)bmp280_calib.dig_P9) * (p >> 13) * (p >> 13)) >> 25;
    var2_p = (((int64_t)bmp280_calib.dig_P8) * p) >> 19;
    p = ((p + var1_p + var2_p) >> 8) + ((int64_t)bmp280_calib.dig_P7 << 4);

    telemetry->pressure = p / 25600.0f; // hPa
    telemetry->pressure /= 10.0f;       // convert to kPa

    // Approximate altitude
    telemetry->altitude = calculate_altitude(telemetry);

    return HAL_OK;
}


