#pragma once
#include "stm32f4xx_hal.h"
#include "telemetry.h"

void reset_alt_dif_buf();
float get_avg_alt_dif();
void update_alt_dif_buf(Telemetry_t *telemetry);
void update_fsm(Telemetry_t *telemetry);
