#include "imu.h"

HAL_StatusTypeDef BNO055_WriteReg(I2C_HandleTypeDef *hi2c, uint8_t reg, uint8_t value)
{
    return HAL_I2C_Mem_Write(hi2c, BNO055_ADDR, reg, I2C_MEMADD_SIZE_8BIT, &value, 1, HAL_MAX_DELAY);
}

HAL_StatusTypeDef BNO055_ReadRegs(I2C_HandleTypeDef *hi2c, uint8_t reg, uint8_t *buffer, uint8_t length)
{
    return HAL_I2C_Mem_Read(hi2c, BNO055_ADDR, reg, I2C_MEMADD_SIZE_8BIT, buffer, length, HAL_MAX_DELAY);
}

HAL_StatusTypeDef init_imu(I2C_HandleTypeDef *hi2c)
{
    uint8_t id = 0;
    if (BNO055_ReadRegs(hi2c, BNO055_CHIP_ID_ADDR, &id, 1) != HAL_OK) return HAL_ERROR;
    if (id != BNO055_CHIP_ID) return HAL_ERROR;

    // Config mode
    BNO055_WriteReg(hi2c, BNO055_OPR_MODE_ADDR, BNO055_OPR_MODE_CONFIG);
    HAL_Delay(25);

    // Units: degrees, m/s²
    BNO055_WriteReg(hi2c, BNO055_UNIT_SEL_ADDR, BNO055_UNIT_SEL_DEFAULT);

    // Normal power mode
    BNO055_WriteReg(hi2c, BNO055_PWR_MODE_ADDR, BNO055_PWR_MODE_NORMAL);
    HAL_Delay(10);

    // NDOF mode
    BNO055_WriteReg(hi2c, BNO055_OPR_MODE_ADDR, BNO055_OPR_MODE_NDOF);
    HAL_Delay(20);

    return HAL_OK;
}

HAL_StatusTypeDef read_imu(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry)
{
    uint8_t buf[6];

    // Accelerometer
    if (BNO055_ReadRegs(hi2c, BNO055_ACC_DATA_X_LSB, buf, 6) != HAL_OK) return HAL_ERROR;
    telemetry->accel_x = (int16_t)(buf[1] << 8 | buf[0]) / 100.0f; // m/s²
    telemetry->accel_y = (int16_t)(buf[3] << 8 | buf[2]) / 100.0f;
    telemetry->accel_z = (int16_t)(buf[5] << 8 | buf[4]) / 100.0f;

    // Gyroscope
    if (BNO055_ReadRegs(hi2c, BNO055_GYR_DATA_X_LSB, buf, 6) != HAL_OK) return HAL_ERROR;
    telemetry->gyro_x = (int16_t)(buf[1] << 8 | buf[0]) / 16.0f; // °/s
    telemetry->gyro_y = (int16_t)(buf[3] << 8 | buf[2]) / 16.0f;
    telemetry->gyro_z = (int16_t)(buf[5] << 8 | buf[4]) / 16.0f;

    // Linear acceleration
//    if (BNO055_ReadRegs(hi2c, BNO055_LIA_DATA_X_LSB, buf, 6) != HAL_OK) return HAL_ERROR;
//    data->linear_accel.x = (int16_t)(buf[1] << 8 | buf[0]) / 100.0f; // m/s²
//    data->linear_accel.y = (int16_t)(buf[3] << 8 | buf[2]) / 100.0f;
//    data->linear_accel.z = (int16_t)(buf[5] << 8 | buf[4]) / 100.0f;

    // Heading (Euler yaw)
    if (BNO055_ReadRegs(hi2c, BNO055_EULER_H_LSB, buf, 2) != HAL_OK)
        return HAL_ERROR;

    telemetry->heading = (int16_t)(buf[1] << 8 | buf[0]) / 16.0f; // degrees

    return HAL_OK;
}
