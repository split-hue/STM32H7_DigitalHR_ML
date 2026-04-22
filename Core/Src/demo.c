#include "demo.h"
#include "ai_platform.h"
#include "strokes.h"
#include "strokes_data.h"
#include <stdlib.h>
#include "main.h"
#include <stdarg.h>
#include <math.h>

extern void Error_Handler(void);

#define PEN_RADIUS    4
#define MAX_LETTERS (sizeof(SLO_ABECEDA) / sizeof(SLO_ABECEDA[0]))
#define MAX_RAW_POINTS 512

static ai_handle network = AI_HANDLE_NULL;
static ai_u8 activations[AI_STROKES_DATA_ACTIVATIONS_SIZE] __attribute__((section(".RAM_D1"), aligned(32)));
static const char* SLO_ABECEDA[] = {
    "A", "B", "C", "Č", "D", "E", "F", "G", "H", "I",
    "J", "K", "L", "M", "N", "O", "P", "R", "S", "Š",
    "T", "U", "V", "Z", "Ž"
};


TS_State_t      TS_State;
TS_Init_t       hTS;
uint8_t         current_target_letter = 0;


typedef struct {
    int16_t x;
    int16_t y;
} Point_t;

static Point_t raw_points[MAX_RAW_POINTS];
static uint16_t raw_points_count = 0;

static float in_data[AI_STROKES_IN_1_SIZE] __attribute__((aligned(32)));
static float out_data[AI_STROKES_OUT_1_SIZE] __attribute__((aligned(32)));



void add_raw_point(int16_t x, int16_t y) {
    if (raw_points_count < MAX_RAW_POINTS) {
        raw_points[raw_points_count].x = x;
        raw_points[raw_points_count].y = y;
        raw_points_count++;
    }
}

void add_stroke_break(void) {
    add_raw_point(-1, -1);
}

void process_strokes_for_ai(float *out) {
    memset(out, 0, AI_STROKES_IN_1_SIZE * sizeof(float));

    if (raw_points_count < 2) return;

    int16_t x_min = 1000, x_max = -1000, y_min = 1000, y_max = -1000;
    for (int i = 0; i < raw_points_count; i++) {
        if (raw_points[i].x != -1) {
            if (raw_points[i].x < x_min) x_min = raw_points[i].x;
            if (raw_points[i].x > x_max) x_max = raw_points[i].x;
            if (raw_points[i].y < y_min) y_min = raw_points[i].y;
            if (raw_points[i].y > y_max) y_max = raw_points[i].y;
        }
    }

    float width = (float)(x_max - x_min) + 1e-8f;
    float height = (float)(y_max - y_min) + 1e-8f;

    int current_p = 0;
    int stroke_idx = 0;

    while (current_p < raw_points_count && stroke_idx < 5) {
        int start = current_p;
        while (current_p < raw_points_count && raw_points[current_p].x != -1) current_p++;
        int n_pts = current_p - start;

        if (n_pts >= 2) {
            float cumdist[n_pts];
            cumdist[0] = 0;
            for (int i = 1; i < n_pts; i++) {
                float dx = raw_points[start+i].x - raw_points[start+i-1].x;
                float dy = raw_points[start+i].y - raw_points[start+i-1].y;
                cumdist[i] = cumdist[i-1] + sqrtf(dx*dx + dy*dy);
            }

            float total_dist = cumdist[n_pts-1];

            for (int i = 0; i < 32; i++) {
                float target_d = (total_dist * i) / 31.0f;
                int seg = 0;
                while (seg < n_pts - 2 && cumdist[seg+1] < target_d) seg++;

                float t = (target_d - cumdist[seg]) / (cumdist[seg+1] - cumdist[seg] + 1e-8f);
                float rx = (float)raw_points[start+seg].x + t * (raw_points[start+seg+1].x - raw_points[start+seg].x);
                float ry = (float)raw_points[start+seg].y + t * (raw_points[start+seg+1].y - raw_points[start+seg].y);

                out[(stroke_idx * 32 + i) * 2 + 0] = (rx - x_min) / width;
                out[(stroke_idx * 32 + i) * 2 + 1] = (ry - y_min) / height;
            }
            stroke_idx++;
        }
        current_p++;
    }
}

//UI, LCD

void canvas_clear(void) {
    raw_points_count = 0;
    UTIL_LCD_FillRect(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H, UTIL_LCD_COLOR_WHITE);
    UTIL_LCD_DrawRect(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H, UTIL_LCD_COLOR_BLACK);
}

void canvas_put_pixel(int x, int y) {
    if (x >= 0 && x < CANVAS_W && y >= 0 && y < CANVAS_H) {
        UTIL_LCD_FillCircle(x + CANVAS_X, y + CANVAS_Y, PEN_RADIUS, UTIL_LCD_COLOR_BLACK);
    }
}

void canvas_draw_line(int x0, int y0, int x1, int y1) {
    int dx = abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
    int dy = -abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
    int err = dx + dy, e2;
    while (1) {
        canvas_put_pixel(x0, y0);
        if (x0 == x1 && y0 == y1) break;
        e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
    }
}

static uint8_t in_canvas(uint16_t x, uint16_t y) {
    return (x >= CANVAS_X && x < (CANVAS_X + CANVAS_W) && y >= CANVAS_Y && y < (CANVAS_Y + CANVAS_H));
}

static uint8_t in_button(uint16_t x, uint16_t y, uint16_t bx, uint16_t by, uint16_t bw, uint16_t bh) {
    return (x >= bx && x < (bx + bw) && y >= by && y < (by + bh));
}

//AI

void ai_init(void) {
    ai_error err;

    //ustvar mrežo
    err = ai_strokes_create(&network, AI_STROKES_DATA_CONFIG);
    if (err.type != AI_ERROR_NONE) {
        Error_Handler();
    }

    //astav uteži in aktivacijo ghh
    const ai_network_params params = { { {
        AI_STROKES_DATA_WEIGHTS(ai_strokes_data_weights_get()),
        AI_STROKES_DATA_ACTIVATIONS(activations)
    } } };

    //inic
    if (!ai_strokes_init(network, &params)) {
        err = ai_strokes_get_error(network); //error če ne uspe
        if (err.type != AI_ERROR_NONE) {
            Error_Handler();
        }
    }
}

uint8_t run_inference(void) {
    if (raw_points_count == 0) return 0xFF;

    process_strokes_for_ai(in_data);
    SCB_CleanDCache_by_Addr((uint32_t*)in_data, sizeof(in_data));

    ai_buffer* inputs = ai_strokes_inputs_get(network, NULL);
    ai_buffer* outputs = ai_strokes_outputs_get(network, NULL);
    inputs->data = AI_HANDLE_PTR(in_data);
    outputs->data = AI_HANDLE_PTR(out_data);

    if (ai_strokes_run(network, inputs, outputs) != 1) return 0xFF;

    float max_val = -1.0f;
    uint8_t max_idx = 0;
    for (uint8_t i = 0; i < AI_STROKES_OUT_1_SIZE; i++) {
        if (out_data[i] > max_val) {
            max_val = out_data[i];
            max_idx = i;
        }
    }
    return max_idx;
}

//GLAVNI

void draw_ui(void) {
	UTIL_LCD_Clear(UTIL_LCD_COLOR_WHITE);
	UTIL_LCD_SetFont(&Font24);
	UTIL_LCD_SetTextColor(UTIL_LCD_COLOR_BLACK);
    char msg[30];
    sprintf(msg, "Narisite: %s", SLO_ABECEDA[current_target_letter]);
    UTIL_LCD_DisplayStringAt(10, 10, (uint8_t*)msg, LEFT_MODE);

    UTIL_LCD_FillRect(BTN_CHECK_X, BTN_CHECK_Y, BTN_CHECK_W, BTN_CHECK_H, UTIL_LCD_COLOR_GREEN);
    UTIL_LCD_SetTextColor(UTIL_LCD_COLOR_WHITE);
    UTIL_LCD_SetBackColor(UTIL_LCD_COLOR_GREEN);
    UTIL_LCD_SetFont(&Font16);
    UTIL_LCD_DisplayStringAt(BTN_CHECK_X + 20, BTN_CHECK_Y + 12, (uint8_t*)"PREVERI", LEFT_MODE);

    UTIL_LCD_FillRect(BTN_CLEAR_X, BTN_CLEAR_Y, BTN_CLEAR_W, BTN_CLEAR_H, UTIL_LCD_COLOR_MAGENTA);
    UTIL_LCD_SetBackColor(UTIL_LCD_COLOR_MAGENTA);
    UTIL_LCD_DisplayStringAt(BTN_CLEAR_X + 25, BTN_CLEAR_Y + 12, (uint8_t*)"POCISTI", LEFT_MODE);

    UTIL_LCD_DrawRect(CANVAS_X, CANVAS_Y, CANVAS_W, CANVAS_H, UTIL_LCD_COLOR_BLACK);
}

void letter_demo(void) {
    if (BSP_LCD_Init(0, LCD_ORIENTATION_LANDSCAPE) != BSP_ERROR_NONE) Error_Handler();
    UTIL_LCD_SetFuncDriver(&LCD_Driver);
    BSP_LCD_DisplayOn(0);

    ai_init();

    hTS.Width = 480;
    hTS.Height = 272;
    hTS.Orientation = TS_SWAP_XY;
    hTS.Accuracy = 5;
    if(BSP_TS_Init(0, &hTS) != BSP_ERROR_NONE) while(1);

    draw_ui();
    canvas_clear();

    uint16_t last_x = 0, last_y = 0;
    uint8_t is_drawing = 0;

    while (1) {
        BSP_TS_GetState(0, &TS_State);

        if (TS_State.TouchDetected) {
            uint16_t tx = (TS_State.TouchX * 480) / 288;
            uint16_t ty = (TS_State.TouchY * 272) / 154;

            if (in_button(tx, ty, BTN_CLEAR_X, BTN_CLEAR_Y, BTN_CLEAR_W, BTN_CLEAR_H)) {
                canvas_clear();
                is_drawing = 0;
                HAL_Delay(200);
            }
            else if (in_button(tx, ty, BTN_CHECK_X, BTN_CHECK_Y, BTN_CHECK_W, BTN_CHECK_H)) {
                if (is_drawing) {
                    add_stroke_break();
                    is_drawing = 0;
                }

                uint8_t res = run_inference();
                //debug-----------------------------------------------------
				int v0 = (int)(out_data[0] * 100);
				int v1 = (int)(out_data[1] * 100);
				int v2 = (int)(out_data[2] * 100);
				int v3 = (int)(out_data[3] * 100);

				char dbg[60];
				sprintf(dbg, "0:%d 1:%d 2:%d", v0, v1, v2);
				UTIL_LCD_FillRect(0, 230, 480, 40, UTIL_LCD_COLOR_WHITE);
				UTIL_LCD_SetTextColor(UTIL_LCD_COLOR_BLACK);
				UTIL_LCD_SetBackColor(UTIL_LCD_COLOR_WHITE);
				UTIL_LCD_SetFont(&Font12);
				UTIL_LCD_DisplayStringAt(0, 235, (uint8_t*)dbg, LEFT_MODE);
				sprintf(dbg, "3:%d res:%d", v3, res);
				UTIL_LCD_DisplayStringAt(0, 250, (uint8_t*)dbg, LEFT_MODE);
				HAL_Delay(3000);
				//-----------------------------

                UTIL_LCD_SetBackColor(UTIL_LCD_COLOR_WHITE);
                UTIL_LCD_SetTextColor(res == current_target_letter ? UTIL_LCD_COLOR_GREEN : UTIL_LCD_COLOR_RED);

                char res_msg[40];
                if (res == current_target_letter) {
                    sprintf(res_msg, "BRAVO! To je %s", SLO_ABECEDA[res]);
                } else {
                    //če model vrne index izven tabele npr. 0xFF >varnostni check
                    if (res < MAX_LETTERS) {
                        sprintf(res_msg, "NAPAKA! Dobil %s", SLO_ABECEDA[res]);
                    } else {
                        sprintf(res_msg, "NAPAKA! Neznan znak");
                    }
                }
                UTIL_LCD_DisplayStringAt(0, 250, (uint8_t*)res_msg, CENTER_MODE);

                HAL_Delay(1500);
                current_target_letter = (current_target_letter + 1) % MAX_LETTERS;
                draw_ui();
                canvas_clear();
                is_drawing = 0;
            }
            else if (in_canvas(tx, ty)) {
                int cx = tx - CANVAS_X;
                int cy = ty - CANVAS_Y;

                if (is_drawing) canvas_draw_line(last_x, last_y, cx, cy);
                else canvas_put_pixel(cx, cy);

                add_raw_point(cx, cy);
                last_x = cx; last_y = cy;
                is_drawing = 1;
            }
        }
        else {
            if (is_drawing) {
                add_stroke_break();
                is_drawing = 0;
            }
        }
        HAL_Delay(10);
    }
}
