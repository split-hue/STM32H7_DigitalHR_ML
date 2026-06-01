#ifndef INC_DEMO_H_
#define INC_DEMO_H_

#include "stdio.h"
#include "string.h"
#include "stm32h7xx_hal.h"
#include "stm32h750b_discovery_lcd.h"
#include "stm32h750b_discovery_ts.h"
#include "stm32_lcd.h"
#include "app_msg.h"

#define CANVAS_X      190
#define CANVAS_Y      40
#define CANVAS_W      280
#define CANVAS_H      220

#define BTN_CHECK_X   20
#define BTN_CHECK_Y   80
#define BTN_CHECK_W   140
#define BTN_CHECK_H   50

#define BTN_CLEAR_X   20
#define BTN_CLEAR_Y   150
#define BTN_CLEAR_W   140
#define BTN_CLEAR_H   50

typedef enum {
    STATE_SHOW_LETTER,
    STATE_DRAWING,
    STATE_RESULT
} AppState;

#ifdef __cplusplus
extern "C" {
#endif

void letter_demo(void);
void canvas_clear(void);
void canvas_to_28x28(float *out);
void uart_print_canvas(void);
void uart_print_results(uint8_t res);
void canvas_to_28x28(float *out);
void itm_print(const char *s);
void itm_printf(const char *fmt, ...);

void logger_print(const log_msg_t *m);

#ifdef __cplusplus
}
#endif

#endif
