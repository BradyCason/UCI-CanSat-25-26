#pragma once
#include <stdint.h>
#include <stdbool.h>

typedef struct {
  bool   valid;
  uint8_t time_hr, time_min, time_sec;
  float  latitude;   // signed, degrees
  float  longitude;  // signed, degrees
  float  altitude_m;
  uint8_t sats;
} gps_sample_t;

void sensor_if_init(void);
void sensor_if_poll(void);

// Optional accessor while debugging
bool sensor_if_get_gps(gps_sample_t *out);
