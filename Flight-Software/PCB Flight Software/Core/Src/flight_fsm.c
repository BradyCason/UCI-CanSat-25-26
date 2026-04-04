#include "flight_fsm.h"
#include <string.h>
#include "servos.h"
#include "main.h"
#include <math.h>

#define CONTAINER_RELEASE_ALT_PERCENTAGE 0.8
#define PAYLOAD_RELEASE_ALT 3

// Liftoff detection variables
uint32_t launch_accel_detected_time = -1;
unsigned int negative_accel_counter = 0;

uint32_t probe_release_time = 0;

void update_fsm(Telemetry_t *telemetry){
	// Eject paraglider
	if (probe_release_time != 0 && telemetry->paraglider_ejected != 1 && HAL_GetTick() - probe_release_time > GLIDER_EJECTION_DELAY){
		Eject_Paraglider();
		telemetry->paraglider_ejected = 1;
		telemetry->paraglider_active = 1;
		probe_release_time = 0;
	}

	if (strcmp(telemetry->state, "LAUNCH_PAD") == 0){
//		if (baro_vz > LAUNCH_THRESHOLD){
//			strcpy(telemetry->state, "ASCENT");
//		}

		if (launch_accel_detected_time == -1){
			// Acceleration not detected yet
			//changed to < for vacuum testing
			if (telemetry->accel_world_z > LAUNCH_ACCEL_THRESHOLD){
				// Positive acceleration detected. Begin period of waiting to get off rail.
				launch_accel_detected_time = HAL_GetTick();
				negative_accel_counter = 0;
			}
		}
		else if (HAL_GetTick() - launch_accel_detected_time > RAIL_DELAY_TIME){
			// In evaluation period. Monitor for any negative acceleration value.
			// If detected, reset the system and begin again.
			if (HAL_GetTick() - launch_accel_detected_time > RAIL_DELAY_TIME + LAUNCH_EVAL_PERIOD_TIME){
				// Enough time passed without negative acceleration. Launch detected
				strcpy(telemetry->state, "ASCENT");
			}
			else if (telemetry->accel_world_z < 0){
				// Negative acceleration detected. Reset system.
				if (++negative_accel_counter >= 5){
					launch_accel_detected_time = -1;
				}
			}
		}
	}
	else if (strcmp(telemetry->state, "ASCENT") == 0){
		if (telemetry->baro_vz < APOGEE_VELO_THRESHOLD){
			strcpy(telemetry->state, "APOGEE");
		}
	}
	else if (strcmp(telemetry->state, "APOGEE") == 0){
		if (telemetry->sent_apogee == 1){
			strcpy(telemetry->state, "DESCENT");
		}
	}
	else if (strcmp(telemetry->state, "DESCENT") == 0){
//		if (telemetry->altitude <= CONTAINER_RELEASE_ALT_PERCENTAGE * telemetry->max_altitude){
		if (telemetry->alt_fused <= CONTAINER_RELEASE_ALT_PERCENTAGE * telemetry->max_altitude){
			strcpy(telemetry->state, "PROBE_RELEASE");
			Release_Container();
			telemetry->container_released = 1;
			probe_release_time = HAL_GetTick();
		}
	}
	else if (strcmp(telemetry->state, "PROBE_RELEASE") == 0){
		// If below release alt or detects landed (In case '0' altitude shifted during flight)
//		if (telemetry->altitude <= PAYLOAD_RELEASE_ALT || get_avg_alt_dif() > LANDED_THRESHOLD){
		if (telemetry->alt_fused <= PAYLOAD_RELEASE_ALT || telemetry->baro_vz > LANDED_VELO_THRESHOLD){
			strcpy(telemetry->state, "PAYLOAD_RELEASE");
			Release_Payload();
			telemetry->payload_released = 1;
		}
	}
	else if (strcmp(telemetry->state, "PAYLOAD_RELEASE") == 0){
		if (telemetry->baro_vz > LANDED_VELO_THRESHOLD && telemetry->sent_payload_release == 1){
			strcpy(telemetry->state, "LANDED");
			telemetry->paraglider_active = 0;
		}
	}
}
