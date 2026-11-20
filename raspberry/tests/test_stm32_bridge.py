import os
import subprocess
from pathlib import Path

import pytest

from cuty.hardware.stm32_bridge import (Boot, Diag, Reply, Stm32Bridge, Telemetry, format_target,
                                        parse_record)

SIM = Path(__file__).resolve().parents[2] / "stm32" / "build" / "sim-pwm" / "cuty_sim"


def test_parse_records():
    assert parse_record("V2,BOOT,WATCHDOG,HSE,84000000,PWM") == Boot("WATCHDOG", "HSE", 84000000, "PWM")
    assert parse_record("V2,ACK,4,TARGET,HEAD_PAN\n") == Reply(4, True, "TARGET", "HEAD_PAN")
    assert parse_record("V2,NAK,7,ARM") == Reply(7, False, "ARM", None)
    t = parse_record("V2,TEL,1210,ACTIVE,NONE,1,188,-250,0,11872,0,3")
    assert isinstance(t, Telemetry)
    assert t.state == "ACTIVE" and t.output_enabled and t.head_pan == pytest.approx(0.188)
    assert t.left_arm == pytest.approx(-0.25) and t.battery_v == pytest.approx(11.872)
    d = parse_record("V2,DIAG,5000,600,700,512,400,300,9000,0,2")
    assert isinstance(d, Diag) and d.stack_free["ServoControlTask"] == 700 and d.tx_overflows == 2
    for bad in ["", "V2,TEL,1,2", "V2,ACK,x,HB", "SIM,PWM,1,1500,1500,1500", "V1,BOOT,a,b,1,c"]:
        assert parse_record(bad) is None


def test_format_target_validates():
    assert format_target("HEAD_PAN", 0.35) == "V2,TARGET,HEAD_PAN,350"
    assert format_target("RIGHT_ARM", -1.0) == "V2,TARGET,RIGHT_ARM,-1000"
    for joint, value in [("EARS", 0.0), ("HEAD_PAN", 1.01), ("LEFT_ARM", float("nan"))]:
        with pytest.raises(ValueError):
            format_target(joint, value)


def test_bridge_sends_heartbeat_and_parses_stream():
    to_pi_r, to_pi_w = os.pipe()
    to_stm_r, to_stm_w = os.pipe()
    reader, writer = os.fdopen(to_pi_r, "rb", buffering=0), os.fdopen(to_stm_w, "wb", buffering=0)
    bridge = Stm32Bridge(reader, writer, heartbeat_period=0.02).start()
    os.write(to_pi_w, b"V2,BOOT,POWER,HSE,84000000,DRYRUN\nnoise\nV2,TEL,200,DISARMED,NONE,0,0,0,0,0,0,0\n")
    assert bridge.wait_state("DISARMED", 1.0)
    assert bridge.boot.build == "DRYRUN"
    bridge.set_target("LEFT_ARM", 0.2)
    sent = os.read(to_stm_r, 4096)
    assert b"V2,HB\n" in sent
    bridge.close()


@pytest.mark.skipif(not SIM.exists(), reason="build the firmware simulator first: make -C stm32 PWM=1 sim")
def test_bridge_against_firmware_simulator():
    proc = subprocess.Popen([str(SIM)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, bufsize=0)
    try:
        bridge = Stm32Bridge(proc.stdout, proc.stdin).start()
        assert bridge.wait_for(lambda b: b.boot is not None, 3)
        assert bridge.wait_state("DISARMED", 2)
        bridge.arm(); bridge.start_motion()
        assert bridge.wait_state("ACTIVE", 2)
        bridge.set_target("HEAD_PAN", -0.3)
        assert bridge.wait_for(lambda b: b.telemetry.head_pan <= -0.29, 6)
        assert any(r.accepted and r.joint == "HEAD_PAN" for r in bridge.replies)
        bridge.stop_heartbeat()  # firmware must fault and release outputs on its own
        assert bridge.wait_for(lambda b: b.telemetry.state == "FAULT" and not b.telemetry.output_enabled, 2)
        assert bridge.telemetry.fault == "HEARTBEAT"
        bridge.close()
    finally:
        proc.kill()
        proc.wait()
