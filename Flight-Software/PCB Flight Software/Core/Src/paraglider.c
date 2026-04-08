#include "paraglider.h"
#include "servos.h"
#include "main.h"
#include <math.h>

float bearing_to_target(float lat1_deg, float lon1_deg,
                        float lat2_deg, float lon2_deg)
{
    float lat1 = lat1_deg * M_PI / 180.0f;
    float lat2 = lat2_deg * M_PI / 180.0f;
    float dLon = (lon2_deg - lon1_deg) * M_PI / 180.0f;

    float y = sin(dLon) * cos(lat2);
    float x = cos(lat1) * sin(lat2)
            - sin(lat1) * cos(lat2) * cos(dLon);

    float bearing = atan2(y, x) * 180.0f / M_PI;

    if (bearing < 0)
        bearing += 360.0f;

    return bearing;   // degrees, compass heading
}

void control_paraglider(Telemetry_t *telemetry){
	// --- PID gains (tune these) ---
	static float Kp = 2.0f;
	static float Ki = 0.05f;
	static float Kd = 0.5f;

	// --- persistent state ---
	static float integral = 0.0f;
	static float prev_error = 0.0f;
	static uint32_t prev_time_glider = 0;

	uint32_t cur_time_us = micros();
	float dt = (float)(cur_time_us - prev_time_glider) * 1e-6f;

    // Find target bearing
    float target_bearing = bearing_to_target(telemetry->gps_latitude,
    		telemetry->gps_longitude, telemetry->target_latitude, telemetry->target_longitude);

    float error = target_bearing - telemetry->heading;
    // Normalize to [-180, 180]
    while (error > 180) error -= 360;
    while (error < -180) error += 360;

    // if absolute value of angle dif < 3 deg, no turning
    if (fabsf(error) < 3.0f) error = 0;

    // --- PID terms ---
    // Integral (with basic anti-windup clamp)
    integral += error * dt;
    float integral_limit = 100.0f;  // tune this
    if (integral > integral_limit) integral = integral_limit;
    if (integral < -integral_limit) integral = -integral_limit;

    // Derivative
    float derivative = (error - prev_error) / dt;

    // PID output
    float turn = Kp * error + Ki * integral + Kd * derivative;

    // Save state
    prev_error = error;

    set_paraglider_steering(turn);
}

void set_paraglider_steering(float turn){
	if (turn == -1000){
		// Inactive position
		Set_Right_Servo_Angle(0);
		Set_Left_Servo_Angle(180);
	} else if (turn == 0) {
		// Both fully extended
		Set_Left_Servo_Angle(170);
		Set_Right_Servo_Angle(10);
	}
	else if (turn < 0) { // Turn left
		// Clamp to a maximum turn amount
		turn = fmaxf(turn, -TURN_MAX);
		Set_Left_Servo_Angle(170 + turn);

		// Fully extended
		Set_Right_Servo_Angle(10);
	}
	else if (turn > 0) { // Turn right
		// Clamp to a maximum turn amount
		turn = fminf(turn, TURN_MAX);
		Set_Right_Servo_Angle(10 + turn);

		// Fully extended
		Set_Left_Servo_Angle(170);
	}
}
