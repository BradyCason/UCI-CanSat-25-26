#pragma once
#include "stm32f4xx_hal.h"
#include "telemetry.h"

// Liftoff detection constants
#define LAUNCH_ACCEL_THRESHOLD 40
#define RAIL_DELAY_TIME 250
#define LAUNCH_EVAL_PERIOD_TIME 100

#define APOGEE_VELO_THRESHOLD -1.0
#define LANDED_VELO_THRESHOLD -0.2

#define GLIDER_EJECTION_DELAY 1000 // ms

void update_fsm(Telemetry_t *telemetry);
