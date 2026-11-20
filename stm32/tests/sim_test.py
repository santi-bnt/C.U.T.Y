"""Scenario test against the FreeRTOS POSIX simulator (real kernel, real adapter).

Drives the simulated USART2 like the Raspberry would and checks the observable
contract: records, state machine, motion, fault reasons, PWM gate, battery
inhibit, task-liveness kill and watchdog reset. Usage:
    make PWM=1 sim && python3 tests/sim_test.py build/sim-pwm/cuty_sim
"""
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


class Sim:
    def __init__(self, exe, env):
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, bufsize=0, env=env)
        self.out, self.err = [], []
        self.lock = threading.Lock()
        self.heartbeat = False
        for stream, sink in ((self.proc.stdout, self.out), (self.proc.stderr, self.err)):
            threading.Thread(target=self._pump, args=(stream, sink), daemon=True).start()
        threading.Thread(target=self._heartbeat, daemon=True).start()

    def _pump(self, stream, sink):
        for raw in iter(stream.readline, b""):
            with self.lock:
                sink.append((time.monotonic(), raw.decode(errors="replace").strip()))

    def _heartbeat(self):
        while self.proc.poll() is None:
            if self.heartbeat:
                self.send("V2,HB")
            time.sleep(0.1)

    def send(self, line):
        try:
            self.proc.stdin.write((line + "\n").encode())
            self.proc.stdin.flush()
        except (BrokenPipeError, ValueError):
            pass
        return time.monotonic()

    def mark(self, sink):
        with self.lock:
            return len(sink)

    def wait(self, sink, predicate, timeout, start=0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                for stamp, line in sink[start:]:
                    if predicate(line):
                        return stamp, line
            time.sleep(0.005)
        raise AssertionError(f"timeout waiting ({timeout}s); last lines: {sink[-6:]}")

    def telemetry(self, start=0):
        with self.lock:
            return [(t, parse_tel(l)) for t, l in self.out[start:] if l.startswith("V2,TEL,")]


def parse_tel(line):
    f = line.split(",")
    return {"ms": int(f[2]), "state": f[3], "reason": f[4], "out": f[5] == "1",
            "pos": [int(x) for x in f[6:9]], "mv": int(f[9]), "rx": int(f[10]), "drop": int(f[11])}


def tel_where(sim, start, cond, timeout):
    return sim.wait(sim.out, lambda l: l.startswith("V2,TEL,") and cond(parse_tel(l)), timeout, start)


def main(exe):
    work = Path(tempfile.mkdtemp(prefix="cuty-sim-"))
    battery, stall = work / "battery_mv", work / "stall"
    battery.write_text("11800")
    env = dict(os.environ, CUTY_SIM_BATTERY_FILE=str(battery), CUTY_SIM_STALL_FILE=str(stall))
    sim = Sim(exe, env)
    results = {}
    try:
        _, boot = sim.wait(sim.out, lambda l: l.startswith("V2,BOOT,"), 3)
        assert boot.endswith(",PWM"), boot
        tel_where(sim, 0, lambda t: t["state"] == "DISARMED" and t["mv"] > 11000, 2)

        # Garbage while DISARMED: counted, never latched as a fault.
        m = sim.mark(sim.out); sim.send("HELLO FROM BOOTING PI")
        tel_where(sim, m, lambda t: t["rx"] >= 1 and t["state"] == "DISARMED", 2)

        # Arming sequence with a live heartbeat.
        sim.heartbeat = True; time.sleep(0.25)
        m = sim.mark(sim.out)
        sim.send("V2,ARM"); sim.send("V2,START")
        sim.wait(sim.out, lambda l: l.startswith("V2,ACK,") and l.endswith(",START"), 1, m)
        tel_where(sim, m, lambda t: t["state"] == "ACTIVE" and t["out"], 1)
        sim.wait(sim.err, lambda l: l.startswith("SIM,PWM,1,"), 1)

        # Motion: TARGET HEAD_PAN 500 -> smooth, no overshoot, PWM follows (1500 + 0.5*400).
        m = sim.mark(sim.out); me = sim.mark(sim.err)
        sent = sim.send("V2,TARGET,HEAD_PAN,500")
        ack_t, _ = sim.wait(sim.out, lambda l: l.endswith(",TARGET,HEAD_PAN") and l.startswith("V2,ACK,"), 1, m)
        results["ACK latency (ms)"] = round((ack_t - sent) * 1000, 1)
        settle_t, _ = tel_where(sim, m, lambda t: t["pos"][0] >= 490, 6)
        results["HEAD_PAN 0 -> 490 milli (s)"] = round(settle_t - sent, 2)
        time.sleep(0.6)
        pans = [t["pos"][0] for _, t in sim.telemetry(m)]
        assert all(b >= a for a, b in zip(pans, pans[1:])), pans
        assert max(pans) <= 500, pans
        sim.wait(sim.err, lambda l: l.startswith("SIM,PWM,1,") and 1690 <= int(l.split(",")[3]) <= 1700, 1, me)
        tels = sim.telemetry(m)
        fw_gaps = [b[1]["ms"] - a[1]["ms"] for a, b in zip(tels, tels[1:])]
        results["telemetry period (firmware ms)"] = round(sum(fw_gaps) / len(fw_gaps), 1)
        assert all(g == 200 for g in fw_gaps), fw_gaps
        wall = tels[-1][0] - tels[0][0]
        results["simulated tick vs wall clock"] = round((tels[-1][1]["ms"] - tels[0][1]["ms"]) / 1000 / wall, 3)
        assert tels[-1][1]["drop"] == 0, tels[-1]

        # Malformed frame while ACTIVE: latched RX fault, outputs released.
        m = sim.mark(sim.out); me = sim.mark(sim.err)
        sent = sim.send("V2,TARGET,HEAD_PAN,1001")
        t_f, _ = tel_where(sim, m, lambda t: t["state"] == "FAULT" and t["reason"] == "RX" and not t["out"], 1)
        t_r, _ = sim.wait(sim.err, lambda l: l.startswith("SIM,PWM,0,"), 1, me)
        results["bad frame -> PWM released (ms)"] = round((t_r - sent) * 1000, 1)

        def rearm():
            mm = sim.mark(sim.out)
            sim.send("V2,RESET"); time.sleep(0.15); sim.send("V2,ARM"); sim.send("V2,START")
            tel_where(sim, mm, lambda t: t["state"] == "ACTIVE" and t["reason"] == "NONE", 1.5)
        rearm()

        # Heartbeat loss: FAULT,HEARTBEAT ~500 ms after the last HB.
        m = sim.mark(sim.out); me = sim.mark(sim.err)
        sim.heartbeat = False; last_hb = time.monotonic()
        t_r, _ = sim.wait(sim.err, lambda l: l.startswith("SIM,PWM,0,"), 2, me)
        tel_where(sim, m, lambda t: t["state"] == "FAULT" and t["reason"] == "HEARTBEAT", 1)
        results["last HB -> PWM released (ms)"] = round((t_r - last_hb) * 1000, 1)
        assert 400 <= (t_r - last_hb) * 1000 <= 750
        sim.heartbeat = True; time.sleep(0.2); rearm()

        # Low battery: 9.5 V sustained -> FAULT,BATTERY, ARM refused until a charged pack.
        m = sim.mark(sim.out); battery.write_text("9500"); t0 = time.monotonic()
        t_b, _ = tel_where(sim, m, lambda t: t["state"] == "FAULT" and t["reason"] == "BATTERY", 4)
        results["9.5 V -> FAULT,BATTERY (s)"] = round(t_b - t0, 2)
        m = sim.mark(sim.out); sim.send("V2,RESET"); time.sleep(0.15); sim.send("V2,ARM")
        sim.wait(sim.out, lambda l: l.startswith("V2,NAK,") and l.endswith(",ARM"), 1, m)
        battery.write_text("12400"); time.sleep(4.0)
        m = sim.mark(sim.out); sim.send("V2,ARM")
        sim.wait(sim.out, lambda l: l.startswith("V2,ACK,") and l.endswith(",ARM"), 1, m)
        sim.send("V2,START"); tel_where(sim, m, lambda t: t["state"] == "ACTIVE", 1)

        # Stuck ServoControlTask: SafetyTask kills PWM, IWDG resets the MCU.
        me = sim.mark(sim.err); stall.write_text("1")
        t_s, _ = sim.wait(sim.err, lambda l: l == "SIM,STALL", 1, me)
        t_k, _ = sim.wait(sim.err, lambda l: l == "SIM,KILL", 1, me)
        t_w, _ = sim.wait(sim.err, lambda l: l == "SIM,WATCHDOG_RESET", 1, me)
        sim.proc.wait(2)
        assert sim.proc.returncode == 3, sim.proc.returncode
        results["stuck control task -> PWM killed (ms)"] = round((t_k - t_s) * 1000, 1)
        results["stuck control task -> watchdog reset (ms)"] = round((t_w - t_s) * 1000, 1)
        assert (t_k - t_s) * 1000 < 120
    finally:
        if sim.proc.poll() is None:
            sim.proc.kill()
    width = max(map(len, results))
    for key, value in results.items():
        print(f"  {key:<{width}}  {value}")
    print("PASS: simulator boot, arming, motion, RX fault, heartbeat loss, battery inhibit, liveness kill, watchdog")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/sim-pwm/cuty_sim")
