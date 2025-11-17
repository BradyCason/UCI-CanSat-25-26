#pragma once
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    bool    valid;
    uint8_t hh, mm, ss;
    float   lat;     // N, degrees
    float   lon;     // E, degrees
    float   alt_m;   // meters
    uint8_t sats;
} gps_sample_t;

void gps_init(void);
bool gps_get_latest(gps_sample_t *out);
