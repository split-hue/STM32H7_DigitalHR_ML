/*
 * syscalls.c
 *
 *  Created on: Apr 16, 2026
 *      Author: Ksenija
 */
#include <sys/stat.h>
#include <stdlib.h>
#include <errno.h>
#include <stdio.h>
#include <signal.h>
#include <time.h>
#include <sys/time.h>
#include <sys/times.h>

/* Tukaj vključi svoj glavni header, da bo syscalls.c poznal huart ročaje */
#include "main.h"

/* Če uporabljaš printf preko UART-a, odkomentiraj spodnjo vrstico in vpiši pravi huart */
// extern UART_HandleTypeDef huart3;

int __io_putchar(int ch) {
    /* Če želiš printf, tukaj pošlji znak čez UART:
       HAL_UART_Transmit(&huart3, (uint8_t *)&ch, 1, 0xFFFF); */
    return ch;
}

int _read(int file, char *ptr, int len) {
    return 0;
}

int _write(int file, char *ptr, int len) {
    int DataIdx;
    for (DataIdx = 0; DataIdx < len; DataIdx++) {
        __io_putchar(*ptr++);
    }
    return len;
}

int _close(int file) {
    return -1;
}

int _fstat(int file, struct stat *st) {
    st->st_mode = S_IFCHR;
    return 0;
}

int _isatty(int file) {
    return 1;
}

int _lseek(int file, int ptr, int dir) {
    return 0;
}

int _getpid(void) {
    return 1;
}

int _kill(int pid, int sig) {
    errno = EINVAL;
    return -1;
}

