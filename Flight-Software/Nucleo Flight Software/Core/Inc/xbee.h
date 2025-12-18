#pragma once
#include "stm32f4xx_hal.h"
#include "telemetry.h"

#define RX_BFR_SIZE 255
#define TX_BFR_SIZE 255

void init_xbee(UART_HandleTypeDef *huart, IRQn_Type IRQn);
void send_packet(UART_HandleTypeDef *huart, Telemetry_t *telemetry);
