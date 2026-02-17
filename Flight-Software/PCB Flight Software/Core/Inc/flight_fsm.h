#pragma once
#include "stm32f4xx_hal.h"
#include "telemetry.h"

// Liftoff detection constants
#define LAUNCH_ACCEL_THRESHOLD 40
#define RAIL_DELAY_TIME 250
#define LAUNCH_EVAL_PERIOD_TIME 250

void reset_alt_dif_buf();
float get_avg_alt_dif();
void update_alt_dif_buf(Telemetry_t *telemetry);
void update_fsm(Telemetry_t *telemetry);
