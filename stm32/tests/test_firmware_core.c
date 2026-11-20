/* Host tests for the firmware-only portable modules: outgoing wire records,
 * battery supervision, liveness supervision, servo calibration and fault
 * reasons. Pure logic; no RTOS, no hardware. */
#include "../App/communication/wire.h"
#include "../App/control/body_control.h"
#include "../App/power/battery.h"
#include "../App/servos/calibration.h"
#include "../App/supervision/liveness.h"
#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>

static void test_wire(void) {
    char line[CUTY_WIRE_LINE_MAX];
    CutyWireReply ack = {42, true, CUTY_TARGET, CUTY_LEFT_ARM};
    assert(cuty_wire_reply(line, sizeof line, &ack) == strlen("V2,ACK,42,TARGET,LEFT_ARM\n"));
    assert(!strcmp(line, "V2,ACK,42,TARGET,LEFT_ARM\n"));
    CutyWireReply nak = {7, false, CUTY_ARM, 0};
    cuty_wire_reply(line, sizeof line, &nak);
    assert(!strcmp(line, "V2,NAK,7,ARM\n"));

    CutyWireTelemetry t = {123456, CUTY_FAULT, CUTY_FAULT_HEARTBEAT_LOST, false,
                           {350, -1000, 0}, 11872, 3, 1};
    cuty_wire_telemetry(line, sizeof line, &t);
    assert(!strcmp(line, "V2,TEL,123456,FAULT,HEARTBEAT,0,350,-1000,0,11872,3,1\n"));

    CutyWireBoot b = {CUTY_RESET_WATCHDOG, false, true, 16000000};
    cuty_wire_boot(line, sizeof line, &b);
    assert(!strcmp(line, "V2,BOOT,WATCHDOG,HSI,16000000,PWM\n"));

    CutyWireDiag d = {5000, {600, 700, 512, 400, 300}, 9000, 0, 2};
    cuty_wire_diag(line, sizeof line, &d);
    assert(!strcmp(line, "V2,DIAG,5000,600,700,512,400,300,9000,0,2\n"));

    /* Too small: nothing partial is ever reported as a line. */
    char tiny[8];
    assert(cuty_wire_reply(tiny, sizeof tiny, &ack) == 0 && tiny[0] == '\0');
    /* Worst-case telemetry still fits the TX line buffer. */
    CutyWireTelemetry worst = {UINT32_MAX, CUTY_DISARMED, CUTY_FAULT_CONTROL_OVERRUN, true,
                               {-1000, -1000, -1000}, UINT32_MAX, UINT32_MAX, UINT32_MAX};
    assert(cuty_wire_telemetry(line, sizeof line, &worst) > 0);

    assert(cuty_wire_milli(0.3504f) == 350 && cuty_wire_milli(-0.0004f) == 0);
    assert(cuty_wire_milli(2.0f) == 1000 && cuty_wire_milli(NAN) == 0);
}

static void test_battery(void) {
    /* Divider 122/22 at the 3.3 V full scale: 4095 -> 18.30 V, 2140 -> ~9.56 V. */
    assert(cuty_battery_mv_from_raw(0) == 0);
    assert(cuty_battery_mv_from_raw(4095) == 18300);
    uint32_t mv = cuty_battery_mv_from_raw(2140);
    assert(mv > 9550 && mv < 9570);

    CutyBattery b; cuty_battery_init(&b);
    uint32_t now = 0;
    /* USB-only bench: absent pack never inhibits. */
    for (unsigned i = 0; i < 50; ++i, now += 100) assert(cuty_battery_update(&b, 0, now) == CUTY_BATTERY_NO_CHANGE);
    assert(b.level == CUTY_BATTERY_ABSENT);

    cuty_battery_init(&b); now = 0;
    assert(cuty_battery_update(&b, 11800, now) == CUTY_BATTERY_NO_CHANGE && b.level == CUTY_BATTERY_OK);
    /* Short servo dips below 9.9 V (filtered) do not trip. */
    for (unsigned i = 0; i < 3; ++i) { now += 100; assert(cuty_battery_update(&b, 7000, now) == CUTY_BATTERY_NO_CHANGE); }
    for (unsigned i = 0; i < 30; ++i) { now += 100; cuty_battery_update(&b, 11800, now); }
    assert(b.level == CUTY_BATTERY_OK);
    /* Sustained 9.6 V: CRITICAL after the filter settles plus 1 s. */
    CutyBatteryEvent e = CUTY_BATTERY_NO_CHANGE; unsigned steps = 0;
    while (e != CUTY_BATTERY_BECAME_CRITICAL) { now += 100; e = cuty_battery_update(&b, 9600, now); assert(++steps < 100); }
    assert(b.level == CUTY_BATTERY_CRITICAL);
    /* Rebound after the load is released (10.6 V) keeps the latch. */
    for (unsigned i = 0; i < 100; ++i) { now += 100; assert(cuty_battery_update(&b, 10600, now) == CUTY_BATTERY_NO_CHANGE); }
    /* Unplugging keeps it latched too. */
    for (unsigned i = 0; i < 100; ++i) { now += 100; assert(cuty_battery_update(&b, 0, now) == CUTY_BATTERY_NO_CHANGE); }
    /* A charged pack (12.4 V) clears it after the filter settles plus 2 s. */
    e = CUTY_BATTERY_NO_CHANGE; steps = 0;
    while (e != CUTY_BATTERY_RECOVERED) { now += 100; e = cuty_battery_update(&b, 12400, now); assert(++steps < 100); }
    assert(b.level == CUTY_BATTERY_OK);
}

static void test_liveness(void) {
    CutyLiveness l; cuty_liveness_init(&l, 50);
    assert(cuty_liveness_check(&l, 1000, 1050));
    assert(cuty_liveness_check(&l, 1001, 1000)); /* beat raced ahead of the read */
    assert(!cuty_liveness_check(&l, 1000, 1051));
    assert(!cuty_liveness_check(&l, 2000, 2000)); /* latched until reset */
    cuty_liveness_init(&l, 50);
    assert(cuty_liveness_check(&l, UINT32_MAX - 10, 20)); /* tick rollover */
}

static void test_calibration(void) {
    const CutyServoCalibration cal[CUTY_AXES] = CUTY_SERVO_CALIBRATION_DEFAULT;
    uint16_t us[CUTY_AXES] = {0, 0, 0};
    const float neutral[CUTY_AXES] = {0, 0, 0};
    assert(cuty_servo_pulses(neutral, cal, us));
    assert(us[0] == 1500 && us[1] == 1500 && us[2] == 1500); /* assembly centre */
    const float ends[CUTY_AXES] = {1, -1, 0.5f};
    assert(cuty_servo_pulses(ends, cal, us) && us[0] == 1900 && us[1] == 1100 && us[2] == 1700);
    CutyServoCalibration rev[CUTY_AXES] = CUTY_SERVO_CALIBRATION_DEFAULT; rev[2].reversed = true;
    assert(cuty_servo_pulses(ends, rev, us) && us[2] == 1300);
    const float bad[CUTY_AXES] = {0, NAN, 0};
    us[0] = 7;
    assert(!cuty_servo_pulses(bad, cal, us) && us[0] == 7); /* all-or-nothing */
    CutyServoCalibration wide[CUTY_AXES] = CUTY_SERVO_CALIBRATION_DEFAULT; wide[0].max_us = 2600;
    assert(!cuty_servo_pulses(neutral, wide, us));
}

static void test_fault_reasons(void) {
    CutyController c; CutyLimits limits[CUTY_AXES];
    for (unsigned i = 0; i < CUTY_AXES; ++i) limits[i] = (CutyLimits){-1, 1, 0.8f, 1.5f};
    assert(cuty_control_init(&c, limits, 500, CUTY_RELEASE_OUTPUT));
    CutyCommand hb = {CUTY_HEARTBEAT, 0, 0}, arm = {CUTY_ARM, 0, 0}, start = {CUTY_START, 0, 0}, reset = {CUTY_RESET, 0, 0};
    assert(cuty_control_command(&c, &hb, 0) && cuty_control_command(&c, &arm, 0) && cuty_control_command(&c, &start, 0));
    cuty_control_tick(&c, 600, 0.02f); /* heartbeat expired */
    assert(c.safety.state == CUTY_FAULT && c.safety.fault_reason == CUTY_FAULT_HEARTBEAT_LOST);
    cuty_control_fault(&c, CUTY_FAULT_LIMIT); /* first reason stays */
    assert(c.safety.fault_reason == CUTY_FAULT_HEARTBEAT_LOST);
    assert(cuty_control_command(&c, &reset, 600) && c.safety.fault_reason == CUTY_FAULT_NONE);
    /* Inhibit (low battery): ARM refused while DISARMED, armed states fault. */
    cuty_control_set_inhibit(&c, true);
    assert(cuty_control_command(&c, &hb, 700) && !cuty_control_command(&c, &arm, 700));
    assert(c.safety.state == CUTY_DISARMED);
    cuty_control_set_inhibit(&c, false);
    assert(cuty_control_command(&c, &arm, 700) && cuty_control_command(&c, &start, 700));
    cuty_control_set_inhibit(&c, true);
    assert(c.safety.state == CUTY_FAULT && c.safety.fault_reason == CUTY_FAULT_LOW_BATTERY);
    assert(!cuty_control_output_requested(&c));
    assert(!strcmp(cuty_fault_name(CUTY_FAULT_LOW_BATTERY), "BATTERY"));
    assert(!strcmp(cuty_state_name(CUTY_READY), "READY"));
}

int main(void) {
    test_wire(); test_battery(); test_liveness(); test_calibration(); test_fault_reasons();
    puts("PASS: wire records, battery supervision, liveness, servo calibration, fault reasons");
    return 0;
}
