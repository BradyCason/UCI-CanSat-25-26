#include "flight_fsm.h"
#include "main.h"
#include <stdio.h>

/* Use your existing helpers; examples shown with uart2_printf + LED toggle.
   Replace bodies with real drivers: servo_open(), pyro_fire(), paraglider_on(), etc. */

extern void uart2_printf(const char *fmt, ...);

/* Stubs you likely already have somewhere */
static void servo_payload_open(void)   { /* open latch */ }
static void servo_payload_close(void)  { /* close latch */ }
static void paraglider_arm(void)       { /* power/arm */ }
static void paraglider_deploy(void)    { /* release */  }
static void egg_release(void)          { /* if separate */ }

void act_on_enter_launch_pad(void) {
  servo_payload_close();
  uart2_printf("[FSM] LAUNCH_PAD\n");
}

void act_on_enter_ascent(void) {
  uart2_printf("[FSM] ASCENT\n");
}

void act_on_enter_apogee(void) {
  uart2_printf("[FSM] APOGEE\n");
}

void act_on_enter_descent(void) {
  uart2_printf("[FSM] DESCENT\n");
  paraglider_arm();               // spin up/enable if required
}

void act_on_enter_probe_release(void) {
  uart2_printf("[FSM] PROBE_RELEASE\n");
  paraglider_deploy();            // chute/paraglider release
  servo_payload_open();           // open door/latch
  egg_release();                  // optional separate actuator
}

void act_on_enter_landed(void) {
  uart2_printf("[FSM] LANDED\n");
  /* e.g., stop telemetry burst, enable beacon-only, etc. */
}
