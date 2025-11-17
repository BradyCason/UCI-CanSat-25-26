#include "sensor_if.h"
#include "main.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>

// ---- External HAL handle (from main.c) ----
extern I2C_HandleTypeDef hi2c1;

// ---- PA1010D over I2C ----
#define PA1010D_ADDRESS   (0x10 << 1)  // 7-bit address shifted for HAL
#define PA_BFR_SIZE       255

// You can send PMTK over I2C as a raw write; not strictly required to get basic NMEA.
static uint8_t PA1010D_MODE[] = "$PMTK314,0,1,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0*28\r\n"; // Enable RMC+GGA
static uint8_t PA1010D_RATE[] = "$PMTK220,1000*1F\r\n"; // 1 Hz

static uint8_t pa_buf[PA_BFR_SIZE];
static char    parse_buf[PA_BFR_SIZE];
static gps_sample_t g_gps;

// -------------- GPS parse helpers (from last year) --------------
static uint8_t set_gps(char* buf, uint8_t order,
                       uint8_t *hr, uint8_t *mn, uint8_t *sc,
                       float *lat, float *lon, float *alt, uint8_t *sats)
{
  char tmp[3] = {0};
  if (strlen(buf) == 0) return 0;

  switch(order) {
    case 0: // STATUS: expect GxGGA
      if (strlen(buf) < 5 || buf[0] != 'G' || buf[2] != 'G' || buf[3] != 'G' || buf[4] != 'A') {
        return 1;
      }
      break;
    case 1: /* TIME (hhmmss.sss) */
      tmp[0] = buf[0]; tmp[1] = buf[1]; tmp[2] = 0;  *hr = (uint8_t)atoi(tmp);
      tmp[0] = buf[2]; tmp[1] = buf[3]; tmp[2] = 0;  *mn = (uint8_t)atoi(tmp);
      tmp[0] = buf[4]; tmp[1] = buf[5]; tmp[2] = 0;  *sc = (uint8_t)atoi(tmp);
      break;
    case 2: // LAT (ddmm.mmmm)
      *lat = (float)(atof(buf) / 100.0);
      break;
    case 3: // LAT DIR
      if (buf[0] == 'S') *lat = -*lat;
      break;
    case 4: // LON (dddmm.mmmm)
      *lon = (float)(atof(buf) / 100.0);
      break;
    case 5: // LON DIR
      if (buf[0] == 'W') *lon = -*lon;
      break;
    case 7: // SATS
      *sats = (uint8_t)atoi(buf);
      break;
    case 9: // ALT (meters)
      *alt = (float)atof(buf);
      break;
    default:
      break;
  }
  return 0;
}

static bool parse_nmea_gga(char *buf, gps_sample_t *out)
{
  // buf does NOT include the initial '$'; fields are comma-separated; '*' ends checksum
  uint8_t i, last = 0, order = 0;
  uint8_t hr=0, mn=0, sc=0, sats=0;
  float lat = 0.f, lon = 0.f, alt = 0.f;

  for (i = 0; i < PA_BFR_SIZE; i++) {
    if (buf[i] == ',' || buf[i] == '*' || buf[i] == '\0') {
      if (last != i) {
        memset(parse_buf, 0, sizeof(parse_buf));
        memcpy(parse_buf, &buf[last], i - last);
        if (set_gps(parse_buf, order, &hr, &mn, &sc, &lat, &lon, &alt, &sats)) {
          return false;
        }
      }
      last = i + 1;
      order++;
      if (buf[i] == '*' || buf[i] == '\0') break;
    }
  }

  out->time_hr = hr; out->time_min = mn; out->time_sec = sc;
  out->latitude = lat; out->longitude = lon; out->altitude_m = alt;
  out->sats = sats;
  out->valid = true;
  return true;
}

// -------------- Low-level I2C read of one NMEA line --------------
static bool gps_read_line_over_i2c(char *out, size_t out_sz)
{
  // Strategy: poll bytes via I2C until we see '$', then accumulate until CR/LF or '*'
  uint8_t c = 0;
  size_t  i = 0;

  // Find '$'
  while (HAL_I2C_Master_Receive(&hi2c1, PA1010D_ADDRESS, &c, 1, 50) == HAL_OK) {
    if (c == '$') break;
  }
  if (c != '$') return false;

  // Capture the rest (without the leading '$'), stop on newline or buffer end
  for (i = 0; i < (out_sz - 1); i++) {
    if (HAL_I2C_Master_Receive(&hi2c1, PA1010D_ADDRESS, &c, 1, 50) != HAL_OK) {
      return false;
    }
    if (c == '\r' || c == '\n') break;
    out[i] = (char)c;
  }
  out[i] = '\0';
  return (i > 0);
}

// -------------- Public API --------------
void sensor_if_init(void)
{
  memset(&g_gps, 0, sizeof(g_gps));

  // Optional: configure PA1010D message set/rate via I2C (module accepts PMTK on both UART/I2C).
  // Not required if defaults are fine.
  (void)HAL_I2C_Master_Transmit(&hi2c1, PA1010D_ADDRESS, PA1010D_MODE, strlen((char*)PA1010D_MODE), 200);
  (void)HAL_I2C_Master_Transmit(&hi2c1, PA1010D_ADDRESS, PA1010D_RATE, strlen((char*)PA1010D_RATE), 200);
}

void sensor_if_poll(void)
{
  // Try to read one full line; if it's a GGA, parse it
  if (gps_read_line_over_i2c((char*)pa_buf, sizeof(pa_buf))) {
    // We only parse GGA to mirror last year's test
    if (pa_buf[0] == 'G' && pa_buf[2] == 'G' && pa_buf[3] == 'G' && pa_buf[4] == 'A') {
      (void)parse_nmea_gga((char*)pa_buf, &g_gps);
    }
  }
}

bool sensor_if_get_gps(gps_sample_t *out)
{
  if (!out) return false;
  *out = g_gps;
  return g_gps.valid;
}
