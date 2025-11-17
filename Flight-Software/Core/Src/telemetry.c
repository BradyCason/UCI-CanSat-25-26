#include "telemetry.h"
#include "app_config.h"
#include <stdarg.h>
#include <stdio.h>

void tel_init(void) { }

void tel_printf(const char *fmt, ...) {
    char buf[256];
    va_list ap; va_start(ap, fmt);
    int n = vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    if (n < 0) return;
    if (n > (int)sizeof(buf)) n = sizeof(buf);
    HAL_UART_Transmit(&APP_UART_DBG, (uint8_t*)buf, n, HAL_MAX_DELAY);
}
