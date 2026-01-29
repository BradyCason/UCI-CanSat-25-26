#pragma once
#include <stdint.h>

typedef struct {
	int8_t mission_time_hr;
	int8_t mission_time_min;
	int8_t mission_time_sec;
	int16_t packet_count;
	char mode;
	char state[14];
	float altitude;
	float temperature;
	float pressure;
	float voltage;
	float current;
	float gyro_x;
	float gyro_y;
	float gyro_z;
	float accel_x;
	float accel_y;
	float accel_z;
	uint8_t gps_time_hr;
	uint8_t gps_time_min;
	uint8_t gps_time_sec;
	float gps_altitude;
	float gps_latitude;
	float gps_longitude;
	float mag_r;
	float mag_p;
	float mag_y;
	uint8_t gps_sats;
	char cmd_echo[64];
	uint8_t container_released;
	uint8_t payload_released;
	uint8_t paraglider_active;
	float target_latitude;
	float target_longitude;
	uint8_t sim_enabled;
	uint8_t telemetry_status;
	float altitude_offset;
	float max_altitude;
	uint8_t sent_apogee; // Helps determine when to switch out of apogee state
	uint8_t sent_payload_release; // Ensure that payload release state is sent because it happens close to landed state
} Telemetry_t;

void init_telemetry(Telemetry_t *telemetry);
void set_cmd_echo(const char *cmd, Telemetry_t *telemetry);
