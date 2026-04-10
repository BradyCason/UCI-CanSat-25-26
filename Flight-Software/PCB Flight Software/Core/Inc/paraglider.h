#pragma once
#include "stm32f4xx_hal.h"
#include "telemetry.h"

#define SERVO_MIN 0
#define SERVO_MAX 180
#define TURN_MAX 170

#define HEADING_WHEN_FACING_NORTH 0.0f

void control_paraglider(Telemetry_t *telemetry);
void set_paraglider_steering(float turn);
