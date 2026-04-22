#pragma once
#include "telemetry.h"

// Complementary filter time constants
#define TAU_VELOCITY   0.2f // seconds
#define TAU_ALTITUDE   0.2f // seconds
#define TAU_BARO_VEL   0.5f // seconds

void transform_accel_to_world(Telemetry_t *telemetry);
void complementary_filter(Telemetry_t* telemetry);
void complementary_filter_init(Telemetry_t *telemetry);
