#include "gps.h"
#include <string.h>
#include <stdlib.h>

#define PA1010D_ADDRESS (0x10 << 1)
#define PA_BFR_SIZE 255

// PA1010D DATA
uint8_t PA1010D_RATE[] = "$PMTK220,1000*1F\r\n";
//uint8_t PA1010D_SAT[] = "$PMTK313,1*2E\r\n";
uint8_t PA1010D_SAT[] = "$PMTK353,1,0,0,0,0*2A\r\n";
uint8_t PA1010D_INIT[] = "$PMTK225,0*2B\r\n";
uint8_t PA1010D_CFG[] = "$PMTK353,1,0,0,0,0*2A\r\n";
uint8_t PA1010D_MODE[] = "$PMTK314,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*29\r\n";
uint8_t PA1010D_SEPERATOR = '$';
HAL_StatusTypeDef pa_ret;
uint8_t pa_buf[PA_BFR_SIZE];
HAL_StatusTypeDef pa_init_ret[5];
uint8_t prev_time = 0;
uint8_t i2cret[128];
char parse_buf[255];
char gps_lat_dir;
char gps_long_dir;
uint32_t time_dif;

uint8_t set_gps(char* buf, uint8_t order, Telemetry_t *telemetry){
	char tmp[2];

	if(strlen(buf)==0)
		return 0;

	switch(order) {
	case 0: //STATUS
		if (strlen(buf)<5 || buf[0] != 'G' || buf[2] != 'G' || buf[3] != 'G' || buf[4] != 'A'){
			return 1;
		}
		break;
	case 1: //TIME
		memcpy(tmp, &buf[0], 2);
		telemetry->gps_time_hr = atoi(tmp);
		memcpy(tmp, &buf[2], 2);
		telemetry->gps_time_min = atoi(tmp);
		memcpy(tmp, &buf[4], 2);
		telemetry->gps_time_sec = atoi(tmp);

		break;
	case 2: //LATITUDE
		telemetry->gps_latitude = atof(buf) / 100;
		break;
	case 3: //LATITUDE_DIR
		gps_lat_dir = *buf;
		if (gps_lat_dir == 'S') {
			telemetry->gps_latitude*= -1;
		}
		break;
	case 4: //LONGITUDE
		telemetry->gps_longitude = atof(buf) / 100;
		break;
	case 5: //LONGITUDE DIR
		gps_long_dir = *buf;
		if (gps_long_dir == 'W') {
			telemetry->gps_longitude*= -1;
		}
		break;
	case 7: //SATS
		telemetry->gps_sats = atoi(buf);
		break;
	case 9: //ALTITUDE
		telemetry->gps_altitude = atof(buf);
		break;
	default:
		break;
	}

	return 0;
}

bool parse_nmea(char *buf, Telemetry_t *telemetry){
	uint8_t i;
	uint8_t last = 0;
	uint8_t order = 0;

	for(i=0; i<255;i++){
		if ( buf[i] == 44 ){
			if (last != i){
				memset(parse_buf, '\000', sizeof parse_buf);
				memcpy(parse_buf, &buf[last], i-last);
				if(set_gps(parse_buf, order, telemetry)){
					return false;
				}
			}
			last = i + 1;
			order = order + 1;
		} else if (buf[i] == 42) {
			break;
		}
	}

	return true;
}

void init_gps(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry)
{
	if (HAL_I2C_IsDeviceReady(hi2c, PA1010D_ADDRESS, 3, 5) != HAL_OK) return;
	uint8_t pa1010d_bytebuf;

	HAL_I2C_Master_Transmit(hi2c, PA1010D_ADDRESS, PA1010D_MODE, strlen( (char *)PA1010D_MODE), 1000);
	HAL_I2C_Master_Transmit(hi2c, PA1010D_ADDRESS, PA1010D_RATE, strlen( (char *)PA1010D_RATE), 1000);
//	pa_init_ret[1] = HAL_I2C_Master_Transmit(hi2c, PA1010D_ADDRESS, PA1010D_INIT, strlen( (char *)PA1010D_INIT), 1000);
//	pa_init_ret[2] = HAL_I2C_Master_Transmit(hi2c, PA1010D_ADDRESS, PA1010D_SAT, strlen( (char *)PA1010D_SAT), 1000);
//	pa_init_ret[3] = HAL_I2C_Master_Transmit(hi2c, PA1010D_ADDRESS, PA1010D_CFG, strlen( (char *)PA1010D_CFG), 1000);

//	HAL_Delay(10000);
	//Wait for stabilization
	for(int j=0; j<10; j++){
		for(int i=0; i<255; i++){
			HAL_I2C_Master_Receive(hi2c, PA1010D_ADDRESS, &pa1010d_bytebuf, 1, HAL_MAX_DELAY);
			if (pa1010d_bytebuf == '$'){
				break;
			}
			pa_buf[i] = pa1010d_bytebuf;
		}
		if (j>5){
			parse_nmea(pa_buf, telemetry);
		}
		HAL_Delay(500);
	}

	flush_gps(hi2c, telemetry);
}

bool read_gps(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry)
{
	if (HAL_I2C_IsDeviceReady(hi2c, PA1010D_ADDRESS, 3, 5) != HAL_OK) return false;

	uint8_t pa_buf_index = 0;
	uint8_t pa_bytebuf = 0;
    bool ret = false;

	/* PA1010D (GPS) */
	if (HAL_I2C_IsDeviceReady(hi2c, PA1010D_ADDRESS, 3, HAL_MAX_DELAY) == HAL_OK){
		for(pa_buf_index=0; pa_buf_index<255; pa_buf_index++){
			HAL_I2C_Master_Receive(hi2c, PA1010D_ADDRESS, &pa_bytebuf, 1, HAL_MAX_DELAY);
			if (pa_bytebuf == '$'){
				ret = true;
				break; // Idea: take away break statement and see what the whole sentence looks like
			}
			pa_buf[pa_buf_index] = pa_bytebuf;
		}
		parse_nmea(pa_buf, telemetry);
	}
	return ret;
}

void flush_gps(I2C_HandleTypeDef *hi2c, Telemetry_t *telemetry){
	while(read_gps(hi2c, telemetry));
}
