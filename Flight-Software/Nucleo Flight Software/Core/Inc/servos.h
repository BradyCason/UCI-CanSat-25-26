#pragma once
#include "stm32f4xx_hal.h"

// Servo Parameters
#define SERVO_MIN_PULSE_WIDTH 700   // 0° (0.5 ms)
#define SERVO_MAX_PULSE_WIDTH 2500  // 180° (2.5 ms)
#define SERVO_FREQUENCY 50

// Define External Timers
extern TIM_HandleTypeDef htim2;

// Define servo timers and channels
#define PAYLOAD_TIM htim2
#define PAYLOAD_CHANNEL TIM_CHANNEL_1
#define CONTAINER_TIM htim2
#define CONTAINER_CHANNEL TIM_CHANNEL_1
#define LEFT_SERVO_TIM htim2
#define LEFT_SERVO_CHANNEL TIM_CHANNEL_1
#define RIGHT_SERVO_TIM htim2
#define RIGHT_SERVO_CHANNEL TIM_CHANNEL_1

// Open and Closed angles
#define PAYLOAD_ANGLE_CLOSED 128 // 128
#define PAYLOAD_ANGLE_OPEN 85 // 90> >80
#define CONTAINER_ANGLE_CLOSED 128 // 128
#define CONTAINER_ANGLE_OPEN 85 // 90> >80

void Init_Servos();
void Release_Payload();
void Reset_Payload();
void Release_Container();
void Reset_Container();
void Set_Left_Servo_Angle(uint8_t angle);
void Set_Right_Servo_Angle(uint8_t angle);
