#include "imu.h"
#include "app_config.h"

bool imu_init(void) {
    // Simple ping to 7-bit IMU address (e.g., BNO055 later @ 0x28 or 0x29).
    // For now we use your placeholder IMU_ADDR_7BIT (0x68).
    uint16_t addr = (IMU_ADDR_7BIT << 1);
    return (HAL_I2C_IsDeviceReady(&APP_I2C_IMU, addr, 2, 5) == HAL_OK);
}

bool imu_read(imu_sample_t *out) {
    // No new IMU yet → report valid=false (or zeros if ping OK)
    if (!out) return false;
    out->valid = false;

    uint16_t addr = (IMU_ADDR_7BIT << 1);
    if (HAL_I2C_IsDeviceReady(&APP_I2C_IMU, addr, 2, 5) == HAL_OK) {
        out->valid = true;  // bus is alive; return zeros for now
        out->ax = out->ay = out->az = 0.f;
        out->gx = out->gy = out->gz = 0.f;
    }
    return out->valid;
}
