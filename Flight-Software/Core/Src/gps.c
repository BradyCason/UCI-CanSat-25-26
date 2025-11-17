#include "gps.h"
#include "app_config.h"
#include <string.h>
#include <stdlib.h>
#include <math.h>

#define RXBUF_SZ 128

static char linebuf[256];
static volatile uint16_t line_len = 0;

static gps_sample_t latest;
static volatile bool have_new = false;

static double nmea_to_degrees(double dm) {
    double deg = floor(dm / 100.0);
    double minutes = dm - deg * 100.0;
    return deg + minutes / 60.0;
}

static void parse_gga(const char *s) {
    // Expect $GPGGA or $GNGGA
    if (strncmp(s, "$GPGGA", 6) && strncmp(s, "$GNGGA", 6)) return;

    // Tokenize (simple, safe)
    char buf[256]; strncpy(buf, s, sizeof(buf)-1); buf[sizeof(buf)-1]=0;
    char *f[16] = {0};
    int i=0; char *tok = strtok(buf, ",");
    while (tok && i < 16) { f[i++] = tok; tok = strtok(NULL, ","); }

    // fields: 1=time, 2=lat,3=N/S, 4=lon,5=E/W, 6=fix, 7=sats, 9=alt
    gps_sample_t g = {0};

    if (i >= 10 && f[6] && atoi(f[6]) > 0) {
        // time hhmmss.sss
        if (f[1] && strlen(f[1]) >= 6) {
            char t[3]={0};
            t[0]=f[1][0]; t[1]=f[1][1]; g.hh = (uint8_t)atoi(t);
            t[0]=f[1][2]; t[1]=f[1][3]; g.mm = (uint8_t)atoi(t);
            t[0]=f[1][4]; t[1]=f[1][5]; g.ss = (uint8_t)atoi(t);
        }
        // latitude
        if (f[2] && *f[2]) {
            double dm = atof(f[2]);
            double val = nmea_to_degrees(dm);
            if (f[3] && *f[3]=='S') val = -val;
            g.lat = (float)val;
        }
        // longitude
        if (f[4] && *f[4]) {
            double dm = atof(f[4]);
            double val = nmea_to_degrees(dm);
            if (f[5] && *f[5]=='W') val = -val;
            g.lon = (float)val;
        }
        if (f[7]) g.sats = (uint8_t)atoi(f[7]);
        if (f[9]) g.alt_m = (float)atof(f[9]);

        g.valid = true;
        latest = g;
        have_new = true;
    }
}

void gps_init(void) {
    static uint8_t rxbuf[RXBUF_SZ];
    HAL_UARTEx_ReceiveToIdle_IT(&APP_UART_GPS, rxbuf, RXBUF_SZ);
}

bool gps_get_latest(gps_sample_t *out) {
    if (!have_new) return false;
    *out = latest;
    have_new = false;
    return true;
}

//// UART IDLE callback – accumulates chars into a line, parse on '\n'
//void HAL_UARTEx_RxEventCallback(UART_HandleTypeDef *huart, uint16_t Size) {
//    if (huart != &APP_UART_GPS || Size == 0) return;
//    uint8_t *data = huart->pRxBuffPtr - Size; // buffer just received
//
//    for (uint16_t i=0; i<Size; ++i) {
//        char c = (char)data[i];
//        if (c == '\r') continue;
//        if (c == '\n') {
//            linebuf[line_len] = '\0';
//            parse_gga(linebuf);
//            line_len = 0;
//        } else if (line_len < sizeof(linebuf)-1) {
//            linebuf[line_len++] = c;
//        } else {
//            line_len = 0; // overflow, reset
//        }
//    }
//
//    // Re-arm reception
//    HAL_UARTEx_ReceiveToIdle_IT(huart, huart->pRxBuffPtr, RXBUF_SZ);
//}
