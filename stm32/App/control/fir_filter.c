#include "fir_filter.h"
#include <math.h>
#include <string.h>

bool cuty_fir_init(CutyFirFilter *filter, const float *coefficients, size_t taps) {
    /* Rechaza coeficientes inválidos antes de copiar el filtro a su buffer fijo. */
    if (!filter || !coefficients || taps == 0U || taps > CUTY_FIR_MAX_TAPS) return false;
    for (size_t i = 0; i < taps; ++i) if (!isfinite(coefficients[i])) return false;
    memset(filter, 0, sizeof(*filter));
    memcpy(filter->coefficients, coefficients, taps * sizeof(float));
    filter->taps = taps;
    return true;
}

void cuty_fir_reset(CutyFirFilter *filter, float seed) {
    if (!filter || !isfinite(seed) || filter->taps == 0U) return;
    for (size_t i = 0; i < filter->taps; ++i) filter->history[i] = seed;
    filter->next = 0U;
}

bool cuty_fir_process(CutyFirFilter *filter, float input, float *output) {
    if (!filter || !output || filter->taps == 0U || !isfinite(input)) return false;
    /* `next` señala la muestra que se reemplaza; el recorrido inverso acumula de reciente a antigua. */
    filter->history[filter->next] = input;
    float sum = 0.0f;
    size_t index = filter->next;
    for (size_t k = 0; k < filter->taps; ++k) {
        sum += filter->coefficients[k] * filter->history[index];
        index = (index == 0U) ? filter->taps - 1U : index - 1U;
    }
    filter->next = (filter->next + 1U == filter->taps) ? 0U : filter->next + 1U;
    if (!isfinite(sum)) return false;
    *output = sum;
    return true;
}
