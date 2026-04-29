/*
 * app_msg.h
 *
 *  Created on: Apr 29, 2026
 *      Author: Ksenja
 */

#ifndef INC_APP_MSG_H_
#define INC_APP_MSG_H_


#include <stdint.h>

typedef enum {
    MSG_HDR,           // glava poročila
    MSG_SAMPLE_RESULT, // rezultat ene inference
    MSG_FINAL,         // končno poročilo
    MSG_CLASS_STAT     // statistika za eno črko
} msg_type_t;

typedef struct {
    msg_type_t type;
    uint32_t   id;
    uint8_t    real_idx;
    uint8_t    pred_idx;
    float      conf;
    uint32_t   cycles;
    uint32_t   duration_ms;
} sample_result_t;

typedef struct {
    msg_type_t type;
    uint32_t   total;
    uint32_t   correct;
    float      acc;
    float      avg_ms;
    float      avg_us;
    uint32_t   total_ms;
} final_report_t;

typedef struct {
    msg_type_t type;
    uint8_t    class_idx;
    float      acc;
} class_stat_t;

typedef struct {
    msg_type_t type;
    union {
        sample_result_t sample;
        final_report_t  final;
        class_stat_t    cls;
    } u;
} log_msg_t;

#endif /* INC_APP_MSG_H_ */
