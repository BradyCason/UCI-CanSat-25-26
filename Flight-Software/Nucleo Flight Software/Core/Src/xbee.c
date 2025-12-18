#include "xbee.h"
#include "main.h"
#include <string.h>

typedef uint8_t bool;

uint8_t rx_packet[RX_BFR_SIZE];
char rx_data[RX_BFR_SIZE];
uint8_t tx_data[TX_BFR_SIZE-18];
uint8_t tx_packet[TX_BFR_SIZE];
uint8_t tx_count;
volatile int32_t last_command_count = -1;

extern uint8_t command_ready;
extern char command_buffer[RX_BFR_SIZE-1];

void init_xbee(UART_HandleTypeDef *huart, IRQn_Type IRQn){
	init_commands();

	HAL_NVIC_EnableIRQ(IRQn);
	HAL_UARTEx_ReceiveToIdle_IT(huart, rx_data, RX_BFR_SIZE);
}

uint8_t calculate_checksum(const char *data) {
	uint8_t checksum = 0;
	while (*data) {
		checksum += *data++;
	}
	return checksum % 256;
}

void send_packet(UART_HandleTypeDef *huart, Telemetry_t *telemetry){

	char packet[512];  // Buffer for packet
	char data[480];    // Buffer for data without checksum

	telemetry->packet_count += 1;

	snprintf(data, sizeof(data),
		"%s,%02d:%02d:%02d,%d,%c,%s,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,%02d:%02d:%02d,%.1f,%.1f,%.1f,%u,%s,%.1f,%s,%s,%s,%.1f,%.1f",
		 TEAM_ID, telemetry->mission_time_hr, telemetry->mission_time_min, telemetry->mission_time_sec, telemetry->packet_count,
		 telemetry->mode, telemetry->state, telemetry->altitude, telemetry->temperature, telemetry->pressure, telemetry->voltage,
		 telemetry->current, -telemetry->gyro_z, telemetry->gyro_x, -telemetry->gyro_y, -telemetry->accel_z, telemetry->accel_x, -telemetry->accel_y,
		 telemetry->gps_time_hr, telemetry->gps_time_min, telemetry->gps_time_sec,
		 telemetry->gps_altitude, telemetry->gps_latitude, telemetry->gps_longitude, telemetry->gps_sats, telemetry->cmd_echo,
		 telemetry->max_altitude, (telemetry->container_released == 1) ? "TRUE" : "FALSE", (telemetry->payload_released == 1) ? "TRUE" : "FALSE",
		 (telemetry->paraglider_active == 1) ? "TRUE" : "FALSE", telemetry->target_latitude, telemetry->target_longitude);

	uint8_t checksum = calculate_checksum(data);
	snprintf(packet, sizeof(packet), "~%s,%u\n", data, checksum);

	// Send the packet using HAL_UART_Transmit
//	HAL_UART_Transmit(huart, (uint8_t*)packet, strlen(packet), HAL_MAX_DELAY);

	int packet_len = strlen(packet);
	int chunk_size = 73;

	for (int i = 0; i < packet_len; i += chunk_size) {
	    int remaining = packet_len - i;
	    int send_len = remaining < chunk_size ? remaining : chunk_size;

	    HAL_UART_Transmit(huart, (uint8_t*)&packet[i], send_len, HAL_MAX_DELAY);

	    if (i + chunk_size < packet_len) {
	        HAL_Delay(40);  // Wait 40ms only if more data remains
	    }
	}

	if (strncmp(telemetry->state, "APOGEE", strlen(telemetry->state)) == 0){
		telemetry->sent_apogee = 1;
	}
	else if (strncmp(telemetry->state, "PAYLOAD_RELEASE", strlen(telemetry->state)) == 0){
		telemetry->sent_payload_release = 1;
	}
}


void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size){
	memcpy(rx_packet, rx_data, Size);
	rx_packet[Size] = '\0';
	memset(rx_data, 0, sizeof(rx_data));

	if (rx_packet[0] == '~') {
		// Calculate where the comma and checksum should be
		char *last_comma = &rx_packet[Size - 3];  // Comma is 3 characters from the end (2 for checksum, 1 for comma)

		// Ensure the expected comma is at the right position
		if (*last_comma == ',') {
			*last_comma = '\0'; // Null-terminate before checksum

			// Extract and convert the received checksum (2 characters after the comma)
			uint8_t received_checksum = (uint8_t)strtol(&rx_packet[Size - 2], NULL, 16);  // Convert checksum to integer
			// Calculate checksum of the data part (after '~' and before comma)
			uint8_t calculated_checksum = calculate_checksum(&rx_packet[1]);

			// Compare calculated checksum with the received one
			if (calculated_checksum == received_checksum && command_ready == 0) {
				// Checksum is valid, and this is new command. Process the command
				strcpy(command_buffer, &rx_packet[1]);
				command_ready = 1;
			}
		}
	}

	HAL_UARTEx_ReceiveToIdle_IT(huart, rx_data, RX_BFR_SIZE);
}
