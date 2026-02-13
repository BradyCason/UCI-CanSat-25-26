#pragma once
#include "stm32f4xx_hal.h"
#include "telemetry.h"

#define SERVO_MIN 0
#define SERVO_MAX 180
#define TURN_MAX 90

void control_paraglider(Telemetry_t *telemetry);
