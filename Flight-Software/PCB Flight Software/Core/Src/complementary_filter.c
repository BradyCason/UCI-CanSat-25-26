#include "complementary_filter.h"
#include "main.h"

uint32_t prev_time_cf = 0;

float prev_baro_alt = 0.0f;  // previous barometer altitude for velocity calculation

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

void complementary_filter(Telemetry_t* telemetry) {
	// Get time since last call
    uint32_t cur_time = micros();
    float dt = (cur_time - prev_time_cf) * 1e-6f;
    if (dt <= 0.0f) return;  // safety check
    if (dt > 0.05f) dt = 0.05f; // Clamp large dt
    prev_time_cf = cur_time;

    // STAGE 1: Velocity Fusion
    // Use gravity-compensated, tilt-corrected vertical acceleration
    telemetry->velocity_world_x += telemetry->accel_world_x * dt;
    telemetry->velocity_world_y += telemetry->accel_world_y * dt;
    telemetry->velocity_world_z += telemetry->accel_world_z * dt;
    // float velocity_imu = velocity_fused + (-Accel_z - 9.81f) * dt;

    // Calculate barometric velocity
    float velocity_baro = (telemetry->altitude - prev_baro_alt) / dt;
    prev_baro_alt = telemetry->altitude;

    // Fuse velocities: 99% IMU, 1% barometer
    telemetry->velocity_world_z = ALPHA_VELOCITY * telemetry->velocity_world_z
				 + (1.0f - ALPHA_VELOCITY) * velocity_baro;

    // STAGE 2: Altitude Fusion
    // Integrate fused velocity to get altitude prediction
    float alt_from_velocity = telemetry->alt_fused + telemetry->velocity_world_z * dt;

    // Fuse altitudes: 95% integrated velocity, 5% raw barometer
    telemetry->alt_fused = ALPHA_ALTITUDE * alt_from_velocity
			  + (1.0f - ALPHA_ALTITUDE) * telemetry->altitude;

    // Damp x and y velocity to reduce drift
    telemetry->velocity_world_x *= 0.999f;
    telemetry->velocity_world_y *= 0.999f;
}
