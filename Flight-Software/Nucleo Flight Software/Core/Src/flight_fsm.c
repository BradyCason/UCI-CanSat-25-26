#include "flight_fsm.h"
#include <string.h>
#include "servos.h"
#include <math.h>

#define LAUNCH_THRESHOLD 5
#define APOGEE_THRESHOLD -0.5
#define LANDED_THRESHOLD -0.2
#define ALT_DIF_BUF_SIZE 5

#define CONTAINER_RELEASE_ALT_PERCENTAGE 0.8
#define PAYLOAD_RELEASE_ALT 3

float alt_dif_buffer[ALT_DIF_BUF_SIZE];
int alt_dif_buffer_idx = 0;
int prev_alt_time = 0;
float prev_alt;

void reset_alt_dif_buf(Telemetry_t *telemetry){
	prev_alt_time = HAL_GetTick();
	for (int i = 0; i < ALT_DIF_BUF_SIZE; ++i){
		alt_dif_buffer[i] = 0;
	}
	prev_alt = telemetry->altitude;
}

float get_avg_alt_dif() {
	float sum = 0;
    float largest = alt_dif_buffer[0];
    float smallest = alt_dif_buffer[0];
    for (int i = 0; i < ALT_DIF_BUF_SIZE; ++i){
    	sum += alt_dif_buffer[i];
    	largest = fmax(largest, alt_dif_buffer[i]);
    	smallest = fmin (smallest, alt_dif_buffer[i]);
    }
    return (sum - largest - smallest) / (ALT_DIF_BUF_SIZE - 2);
}

void update_alt_dif_buf(Telemetry_t *telemetry) {
    float cur_time = HAL_GetTick();
    if (cur_time == prev_alt_time){
    	return;
    }
    alt_dif_buffer[alt_dif_buffer_idx] = (telemetry->altitude - prev_alt) / (cur_time - prev_alt_time) * 1000;
	alt_dif_buffer_idx = (alt_dif_buffer_idx + 1) % ALT_DIF_BUF_SIZE;
	prev_alt_time = cur_time;
	prev_alt = telemetry->altitude;
}

void update_fsm(Telemetry_t *telemetry){
	if (strcmp(telemetry->state, "LAUNCH_PAD") == 0){
		if (get_avg_alt_dif() > LAUNCH_THRESHOLD){
			strcpy(telemetry->state, "ASCENT");
		}
	}
	else if (strcmp(telemetry->state, "ASCENT") == 0){
		if (get_avg_alt_dif() < APOGEE_THRESHOLD){
			strcpy(telemetry->state, "APOGEE");
		}
	}
	else if (strcmp(telemetry->state, "APOGEE") == 0){
		if (telemetry->sent_apogee == 1){
			strcpy(telemetry->state, "DESCENT");
		}
	}
	else if (strcmp(telemetry->state, "DESCENT") == 0){
		if (telemetry->altitude <= CONTAINER_RELEASE_ALT_PERCENTAGE * telemetry->max_altitude){
			strcpy(telemetry->state, "PROBE_RELEASE");
			Release_Container();
			telemetry->container_released = 1;
			telemetry->paraglider_active = 1;
		}
	}
	else if (strcmp(telemetry->state, "PROBE_RELEASE") == 0){
		// If below release alt or detects landed (In case '0' altitude shifted during flight)
		if (telemetry->altitude <= PAYLOAD_RELEASE_ALT || get_avg_alt_dif() > LANDED_THRESHOLD){
			strcpy(telemetry->state, "PAYLOAD_RELEASE");
			Release_Payload();
			telemetry->payload_released = 1;
		}
	}
	else if (strcmp(telemetry->state, "PAYLOAD_RELEASE") == 0){
		if (get_avg_alt_dif() > LANDED_THRESHOLD && telemetry->sent_payload_release == 1){
			strcpy(telemetry->state, "LANDED");
			telemetry->paraglider_active = 0;
		}
	}
}
