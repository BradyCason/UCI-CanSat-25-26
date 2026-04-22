#include "complementary_filter.h"
#include "main.h"
#include <math.h>
#include <stdint.h>
#include <stdbool.h>

static uint64_t prev_time_cf_us = 0;

static float prev_baro_alt = 0.0f;

static bool cf_initialized = false;

void transform_accel_to_world(Telemetry_t *telemetry) {
  // Average IMUs (body frame)
  float ax = telemetry->accel_x;
  float ay = telemetry->accel_y;
  float az = telemetry->accel_z;

  // Quaternion (w, x, y, z)
  float qw = telemetry->qw;
  float qx = telemetry->qx;
  float qy = telemetry->qy;
  float qz = telemetry->qz;

  // Rotation matrix (body → world)
  float R11 = 1.0f - 2.0f*(qy*qy + qz*qz);
  float R12 = 2.0f*(qx*qy - qz*qw);
  float R13 = 2.0f*(qx*qz + qy*qw);

  float R21 = 2.0f*(qx*qy + qz*qw);
  float R22 = 1.0f - 2.0f*(qx*qx + qz*qz);
  float R23 = 2.0f*(qy*qz - qx*qw);

  float R31 = 2.0f*(qx*qz - qy*qw);
  float R32 = 2.0f*(qy*qz + qx*qw);
  float R33 = 1.0f - 2.0f*(qx*qx + qy*qy);

  // Rotate acceleration into world frame
  telemetry->accel_world_x = R11*ax + R12*ay + R13*az;
  telemetry->accel_world_y = R21*ax + R22*ay + R23*az;
  telemetry->accel_world_z = R31*ax + R32*ay + R33*az - 9.81f;
}

void complementary_filter_init(Telemetry_t *telemetry)
{
    float baro_alt = telemetry->altitude;

    prev_time_cf_us = micros();
    prev_baro_alt = baro_alt;

    telemetry->velocity_world_z = 0.0f;

    telemetry->alt_fused = baro_alt;

    cf_initialized = true;
}

void complementary_filter(Telemetry_t* telemetry) {
	if (!cf_initialized) {
		complementary_filter_init(telemetry);
		return;
	}

	uint64_t cur_time_us = micros();
	float dt = (float)(cur_time_us - prev_time_cf_us) * 1e-6f;
	prev_time_cf_us = cur_time_us;

	if (!isfinite(dt) || dt <= 0.0f || dt > 0.1f) {
		return;
	}

	float baro_alt = telemetry->altitude;

	float velocity_baro_raw = (baro_alt - prev_baro_alt) / dt;
	prev_baro_alt = baro_alt;

	float baro_vel_alpha = TAU_BARO_VEL / (TAU_BARO_VEL + dt);
	telemetry->baro_vz =
		baro_vel_alpha * telemetry->baro_vz +
		(1.0f - baro_vel_alpha) * velocity_baro_raw;

	float velocity_imu = telemetry->velocity_world_z +
						 telemetry->accel_world_z * dt;

	float alpha_velocity = TAU_VELOCITY / (TAU_VELOCITY + dt);
	telemetry->velocity_world_z =
		alpha_velocity * velocity_imu +
		(1.0f - alpha_velocity) * telemetry->baro_vz;

	float altitude_pred =
		telemetry->alt_fused + telemetry->velocity_world_z * dt;

	float alpha_altitude = TAU_ALTITUDE / (TAU_ALTITUDE + dt);
	telemetry->alt_fused =
		alpha_altitude * altitude_pred +
		(1.0f - alpha_altitude) * baro_alt;

	if (!isfinite(telemetry->velocity_world_z)) telemetry->velocity_world_z = 0.0f;
	if (!isfinite(telemetry->alt_fused))        telemetry->alt_fused = baro_alt;
}
