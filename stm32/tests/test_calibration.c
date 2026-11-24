#include "../App/control/manual_calibration.h"
#include "../App/communication/uart_protocol.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    CutyCommand command;
    assert(cuty_parse_line("V2,CAL,LEFT_ARM,1500", &command));
    assert(command.kind == CUTY_CALIBRATE && command.axis == CUTY_LEFT_ARM && command.pulse_us == 1500);
    const char *bad[] = {"V2,CAL,LEFT_ARM,-100", "V2,CAL,LEFT_ARM,999", "V2,CAL,J10,1500",
        "V2,CAL,HEAD_PAN,2001", "V2,CAL,HEAD_PAN,15000", "V2,CAL,HEAD_PAN,1500,EXTRA"};
    for (unsigned i = 0; i < sizeof bad / sizeof bad[0]; ++i)
        assert(!cuty_parse_line(bad[i], &command));
    CutyManualCalibration s = {0};
    assert(!cuty_calibration_request(&s, 1, 1400, 0));
    assert(!s.active);
    assert(cuty_calibration_request(&s, 1, 1500, 0));
    assert(!cuty_calibration_request(&s, 0, 1500, 100));
    assert(!cuty_calibration_request(&s, 1, 1510, 99));
    assert(!cuty_calibration_request(&s, 1, 1520, 100));
    assert(cuty_calibration_request(&s, 1, 1510, 100));
    assert(cuty_calibration_request(&s, 1, 1500, 200));
    for (unsigned i = 1; i <= 50; ++i)
        assert(cuty_calibration_request(&s, 1, (uint16_t)(1500 + i * 10), 200 + i * 100));
    assert(!cuty_calibration_request(&s, 1, 2001, 5300));
    assert(!cuty_calibration_request(&s, 1, 999, 5300));
    assert(cuty_calibration_expired(&s, 60000));
    assert(!cuty_calibration_request(&s, 1, 2000, 60000));
    s = (CutyManualCalibration){0};
    assert(cuty_calibration_request(&s, 2, 1500, UINT32_MAX - 99));
    assert(cuty_calibration_request(&s, 2, 1510, 0));
    assert(!cuty_calibration_expired(&s, 200));
    puts("PASS: CAL parser, initial pulse, single axis, step/rate limits, bounds, timeout and rollover");
    return 0;
}
