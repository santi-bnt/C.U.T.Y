#ifndef CUTY_FIR_FILTER_H
#define CUTY_FIR_FILTER_H
#include <stdbool.h>
#include <stddef.h>

#define CUTY_FIR_MAX_TAPS 16U
typedef struct {
    float coefficients[CUTY_FIR_MAX_TAPS];
    float history[CUTY_FIR_MAX_TAPS];
    size_t taps;
    size_t next;
} CutyFirFilter;

bool cuty_fir_init(CutyFirFilter *filter, const float *coefficients, size_t taps);
void cuty_fir_reset(CutyFirFilter *filter, float seed);
bool cuty_fir_process(CutyFirFilter *filter, float input, float *output);
#endif
