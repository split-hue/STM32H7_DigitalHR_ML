#include "demo.h"
#include "ai_platform.h"
#include "strokes.h"
#include "strokes_data.h"
#include <stdlib.h>
#include "main.h"
#include <stdarg.h>
#include <math.h>
#include "app_msg.h"
#include "cmsis_os.h"

extern osMessageQueueId_t logQueueHandle;
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

//*****************************************
#pragma pack(push, 1)
typedef struct {
    uint8_t label;
    uint16_t num_points;
    float points[320];
} TestSample_t;
#pragma pack(pop)


uint8_t run_inference_internal(void);





void run_batch_analysis_serial(uint32_t start_addr, uint32_t num_samples) {
    uint32_t total_correct = 0;
    uint32_t total_duration = 0;
    uint32_t class_correct[25] = {0};
    uint32_t class_total[25] = {0};
    uint64_t total_cycles = 0;

    // glava
    log_msg_t hdr = { .type = MSG_HDR };
    osMessageQueuePut(logQueueHandle, &hdr, 0, osWaitForever);
    osDelay(1);

    uint32_t start_bench_time = HAL_GetTick();

    for (uint32_t i = 0; i < num_samples; i++) {
        uint32_t offset = i * 1283;
        uint8_t *sample_ptr = (uint8_t *)(start_addr + offset);

        uint8_t real_idx = sample_ptr[0];
        memcpy(in_data, &sample_ptr[3], 320 * sizeof(float));

        uint32_t t1 = HAL_GetTick();
        uint32_t start_cycles = DWT->CYCCNT;
        uint8_t predicted_idx = run_inference_internal();
        uint32_t end_cycles = DWT->CYCCNT;
        uint32_t duration = HAL_GetTick() - t1;

        uint32_t diff = end_cycles - start_cycles;
        total_cycles   += diff;
        total_duration += duration;
        class_total[real_idx]++;
        if (predicted_idx == real_idx) {
            total_correct++;
            class_correct[real_idx]++;
        }

        // pošlji rezultat -> logger
        log_msg_t m = {
            .type = MSG_SAMPLE_RESULT,
            .u.sample = {
                .type        = MSG_SAMPLE_RESULT,
                .id          = i,
                .real_idx    = real_idx,
                .pred_idx    = predicted_idx,
                .conf        = out_data[predicted_idx] * 100.0f,
                .cycles      = diff,
                .duration_ms = duration
            }
        };
        // čakanje, če je queue poln (back-pressure -> ne izgubimo podatkov)
        osMessageQueuePut(logQueueHandle, &m, 0, osWaitForever);
        osDelay(1);
    }
    uint32_t end_bench_time = HAL_GetTick();


    float final_acc = (float)total_correct / num_samples * 100.0f;
    float avg_time = (float)total_duration / num_samples;
    float avg_cycles = (float)total_cycles / num_samples;

    log_msg_t fin = {
        .type = MSG_FINAL,
        .u.final = {
            .type     = MSG_FINAL,
            .total    = num_samples,
            .correct  = total_correct,
            .acc      = final_acc,
            .avg_ms   = avg_time,
            .avg_us   = avg_cycles / (SystemCoreClock / 1000000.0f),
            .total_ms = end_bench_time - start_bench_time
        }
    };
    osMessageQueuePut(logQueueHandle, &fin, 0, osWaitForever);
    osDelay(1);

    for (int c = 0; c < 25; c++) {
        if (class_total[c] > 0) {
            log_msg_t cm = {
                .type = MSG_CLASS_STAT,
                .u.cls = {
                    .type      = MSG_CLASS_STAT,
                    .class_idx = (uint8_t)c,
                    .acc       = (float)class_correct[c] / class_total[c] * 100.0f
                }
            };
            osMessageQueuePut(logQueueHandle, &cm, 0, osWaitForever);
            osDelay(1);
        }
    }
}


void logger_print(const log_msg_t *m)
{
    switch (m->type) {
    case MSG_HDR:
        printf("\r\n==========[ test START ]==========\r\n");
        printf("ID;Real;Pred;Conf;Cycles;us\r\n");
        break;
    case MSG_SAMPLE_RESULT: {
        const sample_result_t *s = &m->u.sample;
        float us = (float)s->cycles / (SystemCoreClock / 1000000.0f);
        printf("%lu;%s;%s;%.2f;%lu;%.2f\r\n",
               (unsigned long)s->id,
               SLO_ABECEDA[s->real_idx],
               SLO_ABECEDA[s->pred_idx],
               s->conf, (unsigned long)s->cycles, us);
        break;
    }
    case MSG_FINAL: {
    	const final_report_t *f = &m->u.final;
		printf("~ KONČNO POROČILO ~\r\n");
		printf("Skupno vzorcev:      %lu\r\n", (unsigned long)f->total);
		printf("Pravilnih napovedi:  %lu\r\n", (unsigned long)f->correct);
		printf("Splošna natančnost:  %.2f%%\r\n", f->acc);
		printf("-----------\r\n");
		printf("Povprečen čas (ms):  %.2f ms\r\n", f->avg_ms);
		printf("Povprečen čas (us):  %.2f us\r\n", f->avg_us);
		printf("Skupni čas testa:    %lu ms\r\n", (unsigned long)f->total_ms);
		break;
    }
    case MSG_CLASS_STAT:
        printf("%s;%.1f%%\r\n", SLO_ABECEDA[m->u.cls.class_idx], m->u.cls.acc);
        break;
    }
}
//=========================================================================



//void run_batch_analysis(uint32_t start_address, uint32_t num_samples) {
//    TestSample_t *samples = (TestSample_t *)start_address;
//    uint32_t correct_predictions = 0;
//    uint32_t total_time = 0;
//    char log_msg[100];
//
//    UTIL_LCD_Clear(UTIL_LCD_COLOR_WHITE);
//    UTIL_LCD_SetFont(&Font16);
//    UTIL_LCD_SetTextColor(UTIL_LCD_COLOR_BLACK);
//    UTIL_LCD_DisplayStringAt(0, 10, (uint8_t*)"Analiza v teku...", CENTER_MODE);
//
//    for (uint32_t i = 0; i < num_samples; i++) {
//        memcpy(in_data, samples[i].points, 320 * sizeof(float));
//
//        uint32_t start_tick = HAL_GetTick();
//
//        uint8_t predicted = run_inference_internal();
//
//        uint32_t end_tick = HAL_GetTick();
//        total_time += (end_tick - start_tick);
//
//        if (predicted == samples[i].label) {
//            correct_predictions++;
//        }
//    }
//
//    float accuracy = (float)correct_predictions / num_samples * 100.0f;
//    float avg_time = (float)total_time / num_samples;
//
//    UTIL_LCD_Clear(UTIL_LCD_COLOR_WHITE);
//    sprintf(log_msg, "Natančnost: %.2f%%", accuracy);
//    UTIL_LCD_DisplayStringAt(0, 100, (uint8_t*)log_msg, CENTER_MODE);
//    sprintf(log_msg, "Uspesnih: %lu/%lu", correct_predictions, num_samples);
//    UTIL_LCD_DisplayStringAt(0, 130, (uint8_t*)log_msg, CENTER_MODE);
//    sprintf(log_msg, "Povpr. cas: %.2f ms", avg_time);
//    UTIL_LCD_DisplayStringAt(0, 160, (uint8_t*)log_msg, CENTER_MODE);
//}


uint8_t run_inference_internal(void) {
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

//******************************************************************



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

void letter_demo_run_once(void) {
	run_batch_analysis_serial(0x90100000, 40);
	while(1) {
	        osDelay(1000);
	    }
}

void letter_demo_init(void) {
    if (BSP_LCD_Init(0, LCD_ORIENTATION_LANDSCAPE) != BSP_ERROR_NONE) Error_Handler();
    UTIL_LCD_SetFuncDriver(&LCD_Driver);
    BSP_LCD_DisplayOn(0);

    ai_init();

    hTS.Width = 480;
    hTS.Height = 272;
    hTS.Orientation = TS_SWAP_XY;
    hTS.Accuracy = 5;
    if (BSP_TS_Init(0, &hTS) != BSP_ERROR_NONE) while(1);
}

//void letter_demo(void) {
//    if (BSP_LCD_Init(0, LCD_ORIENTATION_LANDSCAPE) != BSP_ERROR_NONE) Error_Handler();
//    UTIL_LCD_SetFuncDriver(&LCD_Driver);
//    BSP_LCD_DisplayOn(0);
//
//    ai_init();
//
//    hTS.Width = 480;
//    hTS.Height = 272;
//    hTS.Orientation = TS_SWAP_XY;
//    hTS.Accuracy = 5;
//    if(BSP_TS_Init(0, &hTS) != BSP_ERROR_NONE) while(1);

//    draw_ui();
//    canvas_clear();
//
//    uint16_t last_x = 0, last_y = 0;
//    uint8_t is_drawing = 0;
//
//    while (1) {
//        BSP_TS_GetState(0, &TS_State);
//
//        if (TS_State.TouchDetected) {
//            uint16_t tx = (TS_State.TouchX * 480) / 288;
//            uint16_t ty = (TS_State.TouchY * 272) / 154;
//
//            if (in_button(tx, ty, BTN_CLEAR_X, BTN_CLEAR_Y, BTN_CLEAR_W, BTN_CLEAR_H)) {
//                canvas_clear();
//                is_drawing = 0;
//                HAL_Delay(200);
//            }
//            else if (in_button(tx, ty, BTN_CHECK_X, BTN_CHECK_Y, BTN_CHECK_W, BTN_CHECK_H)) {
//                if (is_drawing) {
//                    add_stroke_break();
//                    is_drawing = 0;
//                }
//
//                uint8_t res = run_inference();
//                //debug-----------------------------------------------------
//				int v0 = (int)(out_data[0] * 100);
//				int v1 = (int)(out_data[1] * 100);
//				int v2 = (int)(out_data[2] * 100);
//				int v3 = (int)(out_data[3] * 100);
//
//				char dbg[60];
//				sprintf(dbg, "0:%d 1:%d 2:%d", v0, v1, v2);
//				UTIL_LCD_FillRect(0, 230, 480, 40, UTIL_LCD_COLOR_WHITE);
//				UTIL_LCD_SetTextColor(UTIL_LCD_COLOR_BLACK);
//				UTIL_LCD_SetBackColor(UTIL_LCD_COLOR_WHITE);
//				UTIL_LCD_SetFont(&Font12);
//				UTIL_LCD_DisplayStringAt(0, 235, (uint8_t*)dbg, LEFT_MODE);
//				sprintf(dbg, "3:%d res:%d", v3, res);
//				UTIL_LCD_DisplayStringAt(0, 250, (uint8_t*)dbg, LEFT_MODE);
//				HAL_Delay(3000);
//				//-----------------------------
//
//                UTIL_LCD_SetBackColor(UTIL_LCD_COLOR_WHITE);
//                UTIL_LCD_SetTextColor(res == current_target_letter ? UTIL_LCD_COLOR_GREEN : UTIL_LCD_COLOR_RED);
//
//                char res_msg[40];
//                if (res == current_target_letter) {
//                    sprintf(res_msg, "BRAVO! To je %s", SLO_ABECEDA[res]);
//                } else {
//                    //če model vrne index izven tabele npr. 0xFF >varnostni check
//                    if (res < MAX_LETTERS) {
//                        sprintf(res_msg, "NAPAKA! Dobil %s", SLO_ABECEDA[res]);
//                    } else {
//                        sprintf(res_msg, "NAPAKA! Neznan znak");
//                    }
//                }
//                UTIL_LCD_DisplayStringAt(0, 250, (uint8_t*)res_msg, CENTER_MODE);
//
//                HAL_Delay(1500);
//                current_target_letter = (current_target_letter + 1) % MAX_LETTERS;
//                draw_ui();
//                canvas_clear();
//                is_drawing = 0;
//            }
//            else if (in_canvas(tx, ty)) {
//                int cx = tx - CANVAS_X;
//                int cy = ty - CANVAS_Y;
//
//                if (is_drawing) canvas_draw_line(last_x, last_y, cx, cy);
//                else canvas_put_pixel(cx, cy);
//
//                add_raw_point(cx, cy);
//                last_x = cx; last_y = cy;
//                is_drawing = 1;
//            }
//        }
//        else {
//            if (is_drawing) {
//                add_stroke_break();
//                is_drawing = 0;
//            }
//        }
//        HAL_Delay(10);
//    }
//}


