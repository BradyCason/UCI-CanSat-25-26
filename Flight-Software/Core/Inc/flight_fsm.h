#pragma once
#include <stdint.h>
#include <stdbool.h>

/* Flight states (fixed set used in telemetry too) */
typedef enum {
  FSM_LAUNCH_PAD = 0,
  FSM_ASCENT,
  FSM_APOGEE,
  FSM_DESCENT,
  FSM_PROBE_RELEASE,   // payload / egg / paraglider deployment
  FSM_LANDED
} fsm_state_t;

/* One-shot transition report */
typedef struct {
  bool changed;
  fsm_state_t from, to;
} fsm_event_t;

/* Config knobs (tune per mission guide) */
typedef struct {
  float noise_thresh_mps;        // vertical speed magnitude to count as real motion
  float landing_thresh_mps;      // near-zero vertical speed ⇒ landed
  float apogee_confirm_secs;     // seconds of negative climb to declare apogee
  float release_frac_of_apogee;  // deploy once below this fraction of apogee
  uint8_t deriv_window;          // rolling avg window (seconds)
  float min_valid_alt;           // ignore impossible spikes (m)
  float max_valid_alt;           // clamp to sanity (m)
} fsm_cfg_t;

/* Persistent telemetry snapshot */
typedef struct {
  fsm_state_t state;
  float apogee_m;
  float last_alt_m;
  float vz_mps;                  // filtered vertical speed
} fsm_status_t;

/* API */
void fsm_init(const fsm_cfg_t *cfg);                 // call once at boot
fsm_event_t fsm_update(float altitude_m);            // call at 1 Hz (uses internal clock)
const fsm_status_t* fsm_status(void);                // read-only view

/* Action hooks you IMPLEMENT (called exactly on transitions) */
void act_on_enter_launch_pad(void);
void act_on_enter_ascent(void);
void act_on_enter_apogee(void);
void act_on_enter_descent(void);
void act_on_enter_probe_release(void);
void act_on_enter_landed(void);
