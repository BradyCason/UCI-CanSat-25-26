#include "flight_fsm.h"
#include <string.h>
#include <math.h>

/* ---- static state ---- */
static fsm_cfg_t     C;
static fsm_status_t  S;
static float         ring_alt[10];   // up to 10-second window
static uint8_t       ring_n = 0, ring_i = 0;
static uint8_t       neg_vz_count = 0;

/* clamp helper */
static float clampf(float v, float lo, float hi) {
  if (v < lo) return lo;
  if (v > hi) return hi;
  return v;
}

void fsm_init(const fsm_cfg_t *cfg) {
  C = (fsm_cfg_t){
    .noise_thresh_mps       = 3.0f,
    .landing_thresh_mps     = 0.25f,
    .apogee_confirm_secs    = 3.0f,
    .release_frac_of_apogee = 0.75f,
    .deriv_window           = 3,
    .min_valid_alt          = -200.0f,
    .max_valid_alt          = 40000.0f
  };
  if (cfg) C = *cfg;

  memset(&S, 0, sizeof(S));
  S.state     = FSM_LAUNCH_PAD;
  S.apogee_m  = 0.0f;
  S.last_alt_m= 0.0f;
  S.vz_mps    = 0.0f;
  ring_n = ring_i = neg_vz_count = 0;
}

static void call_enter_action(fsm_state_t st) {
  switch (st) {
    case FSM_LAUNCH_PAD:     act_on_enter_launch_pad();     break;
    case FSM_ASCENT:         act_on_enter_ascent();         break;
    case FSM_APOGEE:         act_on_enter_apogee();         break;
    case FSM_DESCENT:        act_on_enter_descent();        break;
    case FSM_PROBE_RELEASE:  act_on_enter_probe_release();  break;
    case FSM_LANDED:         act_on_enter_landed();         break;
  }
}

fsm_event_t fsm_update(float alt_m_raw) {
  fsm_event_t ev = {0};
  /* sanitize input */
  float a = clampf(alt_m_raw, C.min_valid_alt, C.max_valid_alt);

  /* rolling average altitude over deriv_window secs (1 Hz) */
  if (C.deriv_window > 10) C.deriv_window = 10;
  if (ring_n < C.deriv_window) ring_n++;
  ring_alt[ring_i] = a;
  ring_i = (ring_i + 1) % C.deriv_window;

  float sum = 0.f;
  for (uint8_t k=0;k<ring_n;k++) sum += ring_alt[k];
  float a_filt = sum / (ring_n ? ring_n : 1);

  /* vertical speed ~ (filtered alt - last alt) / 1 s */
  float vz = a_filt - S.last_alt_m;
  S.vz_mps = vz;
  S.last_alt_m = a_filt;

  /* track apogee during flight */
  if (a_filt > S.apogee_m && a_filt < C.max_valid_alt) S.apogee_m = a_filt;

  /* state logic with hysteresis */
  fsm_state_t st = S.state;
  fsm_state_t nxt = st;

  switch (st) {
    case FSM_LAUNCH_PAD:
      if (vz > C.noise_thresh_mps) {
        nxt = FSM_ASCENT;
      }
      break;

    case FSM_ASCENT:
      /* need several consecutive seconds of negative climb before apogee */
      if (vz < -C.noise_thresh_mps) {
        if (++neg_vz_count >= (uint8_t)C.apogee_confirm_secs) {
          nxt = FSM_APOGEE;
          neg_vz_count = 0;
        }
      } else {
        if (vz > 0) neg_vz_count = 0;
      }
      break;

    case FSM_APOGEE:
      nxt = FSM_DESCENT;    /* single-step */
      break;

    case FSM_DESCENT:
      /* deployment once below fraction of apogee (only once) */
      if (S.apogee_m > 10.0f && a_filt <= (C.release_frac_of_apogee * S.apogee_m)) {
        nxt = FSM_PROBE_RELEASE;
        break;
      }
      /* or directly to landed if near-zero vertical speed for long enough */
      if (fabsf(vz) < C.landing_thresh_mps) {
        static uint8_t calm = 0;
        if (++calm >= 5) { nxt = FSM_LANDED; calm = 0; }
      } else {
        /* moving again, reset calm counter */
        static uint8_t calm_dummy = 0; (void)calm_dummy;
      }
      break;

    case FSM_PROBE_RELEASE:
      /* after releasing, resume descent */
      nxt = FSM_DESCENT;
      break;

    case FSM_LANDED:
      /* terminal state */
      break;
  }

  if (nxt != st) {
    ev.changed = true; ev.from = st; ev.to = nxt;
    S.state = nxt;
    call_enter_action(nxt);
  }

  return ev;
}

const fsm_status_t* fsm_status(void) { return &S; }
