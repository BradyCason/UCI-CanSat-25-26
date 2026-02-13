#include "baro.h"

static BMP280_CalibData calib;

float calculate_altitude(Telemetry_t *telemetry) {
	return 44330.77 * (1 - powf(telemetry->pressure / 101.326, 0.1902632)) + telemetry->altitude_offset;
}

static void bmp280_read(I2C_HandleTypeDef *hi2c, uint8_t reg, uint8_t *buf, uint16_t len)
{
    HAL_I2C_Mem_Read(hi2c, BMP280_ADDR, reg, 1, buf, len, HAL_MAX_DELAY);
}

static void bmp280_write(I2C_HandleTypeDef *hi2c, uint8_t reg, uint8_t val)
{
    HAL_I2C_Mem_Write(hi2c, BMP280_ADDR, reg, 1, &val, 1, HAL_MAX_DELAY);
}

static void bmp280_read_calibration(I2C_HandleTypeDef *hi2c)
{
    uint8_t buf[24];
    bmp280_read(hi2c, BMP280_REG_CALIB, buf, 24);

    calib.dig_T1 = (buf[1] << 8) | buf[0];
    calib.dig_T2 = (buf[3] << 8) | buf[2];
    calib.dig_T3 = (buf[5] << 8) | buf[4];

    calib.dig_P1 = (buf[7] << 8) | buf[6];
    calib.dig_P2 = (buf[9] << 8) | buf[8];
    calib.dig_P3 = (buf[11] << 8) | buf[10];
    calib.dig_P4 = (buf[13] << 8) | buf[12];
    calib.dig_P5 = (buf[15] << 8) | buf[14];
    calib.dig_P6 = (buf[17] << 8) | buf[16];
    calib.dig_P7 = (buf[19] << 8) | buf[18];
    calib.dig_P8 = (buf[21] << 8) | buf[20];
    calib.dig_P9 = (buf[23] << 8) | buf[22];
}

HAL_StatusTypeDef init_baro(I2C_HandleTypeDef *hi2c)
{
    uint8_t id;
    bmp280_read(hi2c, BMP280_REG_ID, &id, 1);
    if (id != 0x58)
        return HAL_ERROR;

    bmp280_read_calibration(hi2c);

    /* Config:
     * temp oversampling x1
     * pressure oversampling x4
     * normal mode
     */
    bmp280_write(hi2c, BMP280_REG_CTRL_MEAS, 0x27);

    /* Standby 1000 ms, IIR filter off */
    bmp280_write(hi2c, BMP280_REG_CONFIG, 0xA0);

    return HAL_OK;
}

void read_baro(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry)
{
    uint8_t buf[6];
    bmp280_read(hi2c, BMP280_REG_PRESS_MSB, buf, 6);

    /* Raw ADC values */
    int32_t adc_P = (buf[0] << 12) | (buf[1] << 4) | (buf[2] >> 4);
    int32_t adc_T = (buf[3] << 12) | (buf[4] << 4) | (buf[5] >> 4);

    /* -------- Temperature compensation -------- */
    int32_t var1 = ((((adc_T >> 3) - ((int32_t)calib.dig_T1 << 1)))
                   * ((int32_t)calib.dig_T2)) >> 11;

    int32_t var2 = (((((adc_T >> 4) - ((int32_t)calib.dig_T1))
                     * ((adc_T >> 4) - ((int32_t)calib.dig_T1))) >> 12)
                     * ((int32_t)calib.dig_T3)) >> 14;

    calib.t_fine = var1 + var2;

    telemetry->temperature = (calib.t_fine * 5 + 128) / 256.0f / 100.0f;

    /* -------- Pressure compensation -------- */
    int64_t p;
    int64_t v1 = ((int64_t)calib.t_fine) - 128000;
    int64_t v2 = v1 * v1 * calib.dig_P6;
    v2 += (v1 * calib.dig_P5) << 17;
    v2 += ((int64_t)calib.dig_P4) << 35;
    v1 = ((v1 * v1 * calib.dig_P3) >> 8) + ((v1 * calib.dig_P2) << 12);
    v1 = (((((int64_t)1) << 47) + v1) * calib.dig_P1) >> 33;

    if (v1 == 0)
        return;

    p = 1048576 - adc_P;
    p = (((p << 31) - v2) * 3125) / v1;
    v1 = (calib.dig_P9 * (p >> 13) * (p >> 13)) >> 25;
    v2 = (calib.dig_P8 * p) >> 19;
    p = ((p + v1 + v2) >> 8) + (((int64_t)calib.dig_P7) << 4);

    telemetry->pressure = (float)p / 256.0f / 1000.0f; // kPa

    /* -------- Altitude -------- */
    telemetry->altitude = calculate_altitude(telemetry);
}
