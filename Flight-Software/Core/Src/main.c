/* USER CODE BEGIN Header */
/**
  * @file    main.c
  * @brief   Simple BNO055 + BMP280/BME280 I2C sensor test + flight FSM demo.
  *
  *          I2C1 on PB8 (SCL) / PB9 (SDA)
  *          USART2 on PA2 (TX) / PA3 (RX) @ 115200
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"

/* USER CODE BEGIN Includes */
#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>
#include "flight_fsm.h"
/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */
/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */

/* ---- BNO055 ---- */
#define BNO055_ADDR_7BIT        0x28u            /* use 0x29 if ADR pin is high */
#define BNO055_I2C_ADDR         (BNO055_ADDR_7BIT << 1)
#define BNO055_REG_CHIP_ID      0x00u
#define BNO055_EXPECTED_ID      0xA0u

/* ---- BMP280 / BME280 ---- */
#define BMP280_ADDR1_7BIT       0x76u            /* SDO low  -> 0x76 */
#define BMP280_ADDR2_7BIT       0x77u            /* SDO high -> 0x77 */

#define BMP280_I2C_ADDR1        (BMP280_ADDR1_7BIT << 1)
#define BMP280_I2C_ADDR2        (BMP280_ADDR2_7BIT << 1)

#define BMP280_REG_ID           0xD0u
#define BMP280_ID_BMP280        0x58u
#define BMP280_ID_BME280        0x60u

#define BMP280_REG_TEMP_MSB     0xFAu           /* temp[19:12] */
/* then LSB, XLSB */

/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */
/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/
I2C_HandleTypeDef hi2c1;
UART_HandleTypeDef huart2;

/* USER CODE BEGIN PV */
/* These are what you’ll watch in Live Expressions. */
void uart2_printf(const char *fmt, ...)
{
  char buf[128];
  va_list ap;
  va_start(ap, fmt);
  int n = vsnprintf(buf, sizeof(buf), fmt, ap);
  va_end(ap);

  if (n <= 0) return;
  if (n > (int)sizeof(buf)) n = sizeof(buf);

  HAL_UART_Transmit(&huart2, (uint8_t*)buf, (uint16_t)n, 100);
}
volatile HAL_StatusTypeDef g_bno055_status      = HAL_ERROR;
volatile uint8_t           g_bno055_chip_id     = 0;

volatile HAL_StatusTypeDef g_bmp280_status      = HAL_ERROR;
volatile uint8_t           g_bmp280_chip_id     = 0;
volatile uint8_t           g_bmp280_addr_in_use = 0;   /* 0x76 or 0x77 when found */
volatile int32_t           g_bmp280_temp_raw    = 0;   /* 20-bit raw temperature */

/* For FSM debugging */
volatile float             g_fsm_altitude_m     = 0.0f;
volatile int32_t           g_fsm_state          = 0;
volatile float             g_fsm_apogee_m       = 0.0f;
volatile float             g_fsm_vz_mps         = 0.0f;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
static void MX_GPIO_Init(void);
static void MX_I2C1_Init(void);
static void MX_USART2_UART_Init(void);

/* USER CODE BEGIN PFP */
static void BNO055_TestOnce(void);
static void BMP280_TestOnce(void);
static void flight_init(void);
static float simulate_altitude_profile(void);
/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */

static void BNO055_TestOnce(void)
{
  uint8_t id = 0;

  g_bno055_status = HAL_I2C_Mem_Read(&hi2c1,
                                     BNO055_I2C_ADDR,
                                     BNO055_REG_CHIP_ID,
                                     I2C_MEMADD_SIZE_8BIT,
                                     &id,
                                     1,
                                     100);

  g_bno055_chip_id = id;
}

static void BMP280_TestOnce(void)
{
  uint8_t  id  = 0;
  uint8_t  buf[3];
  uint16_t addr_list[2] = { BMP280_I2C_ADDR1, BMP280_I2C_ADDR2 };

  g_bmp280_status      = HAL_ERROR;
  g_bmp280_chip_id     = 0;
  g_bmp280_temp_raw    = 0;
  g_bmp280_addr_in_use = 0;

  /* Try both possible addresses (0x76, 0x77) */
  for (int i = 0; i < 2; ++i)
  {
    uint16_t addr = addr_list[i];

    /* Read chip ID */
    HAL_StatusTypeDef st = HAL_I2C_Mem_Read(&hi2c1,
                                            addr,
                                            BMP280_REG_ID,
                                            I2C_MEMADD_SIZE_8BIT,
                                            &id,
                                            1,
                                            100);

    if (st != HAL_OK)
    {
      continue;   /* try other address */
    }

    /* We got *some* response; record it */
    g_bmp280_status      = HAL_OK;
    g_bmp280_chip_id     = id;
    g_bmp280_addr_in_use = (uint8_t)(addr >> 1);   /* store 7-bit addr: 0x76/0x77 */

    /* Read raw temperature (3 bytes, 20-bit value) */
    st = HAL_I2C_Mem_Read(&hi2c1,
                          addr,
                          BMP280_REG_TEMP_MSB,
                          I2C_MEMADD_SIZE_8BIT,
                          buf,
                          3,
                          100);

    if (st == HAL_OK)
    {
      g_bmp280_temp_raw =
          ((int32_t)buf[0] << 12) |
          ((int32_t)buf[1] << 4)  |
          ((int32_t)buf[2] >> 4);
    }
    else
    {
      g_bmp280_status = st;
    }

    break;  /* stop after the first address that replies */
  }
}


/* FSM config + init */
static void flight_init(void)
{
  fsm_cfg_t cfg = {
    .noise_thresh_mps       = 3.0f,
    .landing_thresh_mps     = 0.25f,
    .apogee_confirm_secs    = 3.0f,
    .release_frac_of_apogee = 0.75f,
    .deriv_window           = 3,
    .min_valid_alt          = -200.0f,
    .max_valid_alt          = 40000.0f
  };
  fsm_init(&cfg);
}

/* For now we simulate a simple flight profile in altitude (meters)
 * so you can see the FSM transitions without real baro altitude yet. */
static float simulate_altitude_profile(void)
{
  static float alt = 0.0f;
  static int   phase = 0;
  static uint32_t hold_counter = 0;

  switch (phase)
  {
    case 0: /* launch pad: stay for 5 s */
      if (++hold_counter >= 5) {
        hold_counter = 0;
        phase = 1;
      }
      break;

    case 1: /* ascent up to ~300 m */
      alt += 20.0f;
      if (alt >= 300.0f) {
        alt = 300.0f;
        phase = 2;
      }
      break;

    case 2: /* small coast at apogee for 3 s */
      if (++hold_counter >= 3) {
        hold_counter = 0;
        phase = 3;
      }
      break;

    case 3: /* descent back to 0 */
      alt -= 20.0f;
      if (alt <= 0.0f) {
        alt = 0.0f;
        phase = 4;
      }
      break;

    case 4: /* landed – stay at 0 */
    default:
      alt = 0.0f;
      break;
  }

  return alt;
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* Reset of all peripherals, Initializes tg_bno055_statushe Flash interface and the Systick. */
  HAL_Init();

  /* Configure the system clock (HSI 16 MHz, no PLL) */
  SystemClock_Config();

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_I2C1_Init();
  MX_USART2_UART_Init();

  /* USER CODE BEGIN 2 */
  flight_init();
  uart2_printf("BOOT: BNO055/BMP280 + FSM demo\r\n");
  /* USER CODE END 2 */

  uint32_t last_fsm = HAL_GetTick();

  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* 1) keep your sensor tests running for Live Expressions */
    BNO055_TestOnce();
    BMP280_TestOnce();

    /* 2) once per second, update the flight FSM with altitude (simulated for now) */
    uint32_t now = HAL_GetTick();
    if (now - last_fsm >= 1000U) {
      last_fsm += 1000U;

      float alt_m = simulate_altitude_profile();
      g_fsm_altitude_m = alt_m;

      fsm_event_t ev = fsm_update(alt_m);
      const fsm_status_t *st = fsm_status();

      g_fsm_state    = (int32_t)st->state;
      g_fsm_apogee_m = st->apogee_m;
      g_fsm_vz_mps   = st->vz_mps;

      /* heartbeat + debug print */
      HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
      uart2_printf("ALT=%.1f Vz=%.2f APO=%.1f ST=%ld%s\r\n",
                   alt_m, st->vz_mps, st->apogee_m,
                   (long)st->state,
                   ev.changed ? " *" : "");
    }

    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    /* small delay so we aren't hammering I2C too hard */
    HAL_Delay(10);
    /* USER CODE END 3 */
  }
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  __HAL_RCC_PWR_CLK_ENABLE();
  __HAL_PWR_VOLTAGESCALING_CONFIG(PWR_REGULATOR_VOLTAGE_SCALE1);

  RCC_OscInitStruct.OscillatorType      = RCC_OSCILLATORTYPE_HSI;
  RCC_OscInitStruct.HSIState            = RCC_HSI_ON;
  RCC_OscInitStruct.HSICalibrationValue = RCC_HSICALIBRATION_DEFAULT;
  RCC_OscInitStruct.PLL.PLLState        = RCC_PLL_NONE;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType      = RCC_CLOCKTYPE_HCLK |
                                     RCC_CLOCKTYPE_SYSCLK |
                                     RCC_CLOCKTYPE_PCLK1 |
                                     RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource   = RCC_SYSCLKSOURCE_HSI;
  RCC_ClkInitStruct.AHBCLKDivider  = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_0) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief I2C1 Initialization Function
  * @param None
  * @retval None
  *
  * Uses PB8 (SCL) / PB9 (SDA) – matches your stm32f4xx_hal_msp.c
  */
static void MX_I2C1_Init(void)
{
  hi2c1.Instance             = I2C1;
  hi2c1.Init.ClockSpeed      = 100000;
  hi2c1.Init.DutyCycle       = I2C_DUTYCYCLE_2;
  hi2c1.Init.OwnAddress1     = 0;
  hi2c1.Init.AddressingMode  = I2C_ADDRESSINGMODE_7BIT;
  hi2c1.Init.DualAddressMode = I2C_DUALADDRESS_DISABLE;
  hi2c1.Init.OwnAddress2     = 0;
  hi2c1.Init.GeneralCallMode = I2C_GENERALCALL_DISABLE;
  hi2c1.Init.NoStretchMode   = I2C_NOSTRETCH_DISABLE;
  if (HAL_I2C_Init(&hi2c1) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief USART2 Initialization Function
  * @param None
  * @retval None
  *
  * PA2 (TX) / PA3 (RX), 115200 8N1
  */
static void MX_USART2_UART_Init(void)
{
  huart2.Instance          = USART2;
  huart2.Init.BaudRate     = 115200;
  huart2.Init.WordLength   = UART_WORDLENGTH_8B;
  huart2.Init.StopBits     = UART_STOPBITS_1;
  huart2.Init.Parity       = UART_PARITY_NONE;
  huart2.Init.Mode         = UART_MODE_TX_RX;
  huart2.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
  huart2.Init.OverSampling = UART_OVERSAMPLING_16;
  if (HAL_UART_Init(&huart2) != HAL_OK)
  {
    Error_Handler();
  }
}

/**
  * @brief GPIO Initialization Function
  * @param None
  * @retval None
  */
static void MX_GPIO_Init(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  __HAL_RCC_GPIOA_CLK_ENABLE();
  __HAL_RCC_GPIOB_CLK_ENABLE();

  /* PA5 as user LED (heartbeat) */
  GPIO_InitStruct.Pin   = GPIO_PIN_5;
  GPIO_InitStruct.Mode  = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull  = GPIO_NOPULL;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

  HAL_GPIO_WritePin(GPIOA, GPIO_PIN_5, GPIO_PIN_RESET);
}

/**
  * @brief  Error Handler
  * @retval None
  */
void Error_Handler(void)
{
  __disable_irq();
  while (1)
  {
    /* optional: fast blink LED to indicate fault */
    HAL_GPIO_TogglePin(GPIOA, GPIO_PIN_5);
    HAL_Delay(100);
  }
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  (void)file;
  (void)line;
}
#endif
