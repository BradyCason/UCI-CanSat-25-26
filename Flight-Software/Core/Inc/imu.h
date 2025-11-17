#pragma once
#include <stdbool.h>

typedef struct {
    bool  valid;
    float ax, ay, az;
    float gx, gy, gz;
} imu_sample_t;

bool imu_init(void);
bool imu_read(imu_sample_t *out);
