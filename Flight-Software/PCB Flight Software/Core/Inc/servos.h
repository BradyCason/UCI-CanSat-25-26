#ifndef SERVOS_H
#define SERVOS_H

#include "stm32f4xx_hal.h"

// Servo timing constants
#define SERVO_MIN_PULSE_WIDTH 1000  // Minimum pulse width in microseconds (0°)
#define SERVO_MAX_PULSE_WIDTH 2000  // Maximum pulse width in microseconds (180°)
#define SERVO_FREQUENCY 50          // Servo frequency in Hz

// Timer and channel definitions - CHANGED TO TIM3
#define PAYLOAD_TIM htim3
#define PAYLOAD_CHANNEL TIM_CHANNEL_1

#define CONTAINER_TIM htim3
#define CONTAINER_CHANNEL TIM_CHANNEL_2

#define LEFT_SERVO_TIM htim3
#define LEFT_SERVO_CHANNEL TIM_CHANNEL_1

#define RIGHT_SERVO_TIM htim3
#define RIGHT_SERVO_CHANNEL TIM_CHANNEL_2

// Servo angle definitions
#define PAYLOAD_ANGLE_OPEN 90
#define PAYLOAD_ANGLE_CLOSED 0

#define CONTAINER_ANGLE_OPEN 90
#define CONTAINER_ANGLE_CLOSED 0

// External timer handle
extern TIM_HandleTypeDef htim3;

// Function prototypes
void Set_Servo_Angle(TIM_HandleTypeDef *htim, uint32_t channel, uint8_t angle);
void Init_Servos(void);
void Release_Payload(void);
void Reset_Payload(void);
void Release_Container(void);
void Reset_Container(void);
void Set_Left_Servo_Angle(uint8_t angle);
void Set_Right_Servo_Angle(uint8_t angle);

#endif // SERVOS_H
