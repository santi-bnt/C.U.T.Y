"""Boot the real Cortex-M4F image in QEMU (netduinoplus2, an STM32F405 board
model) and talk to it over USART2, like the Raspberry would.

What this proves: the vector table, startup, FreeRTOS ARM_CM4F port, NVIC
priorities, USART2 RX/TX interrupts, the CMSIS-RTOS2 layer and every task run
together on an emulated Cortex-M4. What it cannot prove: the F401 clock tree,
TIM4 PWM pins, ADC and IWDG (QEMU does not model them for this board), real
timing margins, or anything electrical. Usage:
    make qemu && python3 tests/qemu_test.py build/qemu/cuty.elf
"""
import socket
import subprocess
import sys
import time


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class Link:
    def __init__(self, port):
        deadline = time.monotonic() + 5
        while True:
            try:
                self.sock = socket.create_connection(("127.0.0.1", port), timeout=1)
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.05)
        self.sock.settimeout(0.02)
        self.buf, self.lines = b"", []

    def pump(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            try:
                data = self.sock.recv(4096)
                if not data:
                    raise AssertionError("QEMU closed the serial link")
                self.buf += data
            except socket.timeout:
                pass
            while b"\n" in self.buf:
                line, self.buf = self.buf.split(b"\n", 1)
                self.lines.append((time.monotonic(), line.decode(errors="replace")))

    def send(self, line):
        self.sock.sendall((line + "\n").encode())
        return time.monotonic()

    def wait(self, predicate, timeout, start=0, heartbeat=False):
        end = time.monotonic() + timeout
        next_hb = 0.0
        while time.monotonic() < end:
            if heartbeat and time.monotonic() >= next_hb:
                self.send("V2,HB"); next_hb = time.monotonic() + 0.1
            self.pump(0.02)
            for stamp, line in self.lines[start:]:
                if predicate(line):
                    return stamp, line
        raise AssertionError(f"timeout; last lines: {self.lines[-6:]}")


def tel(line):
    f = line.split(",")
    return {"ms": int(f[2]), "state": f[3], "reason": f[4], "out": f[5] == "1", "pos": [int(x) for x in f[6:9]]}


def is_tel(cond):
    return lambda l: l.startswith("V2,TEL,") and cond(tel(l))


def main(elf):
    port = free_port()
    qemu = subprocess.Popen(["qemu-system-arm", "-M", "netduinoplus2", "-nographic", "-monitor", "none",
                             "-serial", "null", "-serial", f"tcp:127.0.0.1:{port},server=on,wait=on",
                             "-kernel", elf], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    results = {}
    try:
        link = Link(port)
        _, boot = link.wait(lambda l: l.startswith("V2,BOOT,"), 5)
        results["boot record"] = boot
        link.wait(is_tel(lambda t: t["state"] == "DISARMED"), 2)

        m = len(link.lines)
        link.send("V2,HB"); link.send("V2,ARM"); sent = link.send("V2,START")
        t_ack, _ = link.wait(lambda l: l.startswith("V2,ACK,") and l.endswith(",START"), 1, m, True)
        results["START -> ACK (ms)"] = round((t_ack - sent) * 1000, 1)
        link.wait(is_tel(lambda t: t["state"] == "ACTIVE"), 1, m, True)

        m = len(link.lines)
        link.send("V2,TARGET,LEFT_ARM,-400")
        link.wait(lambda l: l.startswith("V2,ACK,") and l.endswith(",TARGET,LEFT_ARM"), 1, m, True)
        link.wait(is_tel(lambda t: t["pos"][1] <= -390), 6, m, True)
        arm = [tel(l)["pos"][1] for _, l in link.lines[m:] if l.startswith("V2,TEL,")]
        assert all(b <= a for a, b in zip(arm, arm[1:])) and min(arm) >= -400, arm
        stamps = [tel(l)["ms"] for _, l in link.lines[m:] if l.startswith("V2,TEL,")]
        assert all(b - a == 200 for a, b in zip(stamps, stamps[1:])), stamps
        results["LEFT_ARM 0 -> -390 milli, monotonic"] = f"{len(arm)} records"
        assert not any(tel(l)["out"] for _, l in link.lines if l.startswith("V2,TEL,")), "dry-run must never enable PWM"

        m = len(link.lines); last = time.monotonic()
        t_f, _ = link.wait(is_tel(lambda t: t["state"] == "FAULT" and t["reason"] == "HEARTBEAT"), 2, m)
        results["last HB -> FAULT,HEARTBEAT seen (ms)"] = round((t_f - last) * 1000, 1)

        m = len(link.lines)
        link.send("V2,RESET"); link.send("V2,HB"); link.send("V2,ARM"); link.send("V2,START")
        link.wait(is_tel(lambda t: t["state"] == "ACTIVE" and t["reason"] == "NONE"), 1.5, m, True)
        m = len(link.lines)
        link.send("V2,TARGET,HEAD_PAN,12x")
        link.wait(is_tel(lambda t: t["state"] == "FAULT" and t["reason"] == "RX"), 1, m, True)
        results["malformed TARGET while ACTIVE"] = "FAULT,RX"
    finally:
        qemu.kill(); qemu.wait()
    width = max(map(len, results))
    for key, value in results.items():
        print(f"  {key:<{width}}  {value}")
    print("PASS: ARM image in QEMU: boot, USART2 IRQ RX/TX, arming, motion, heartbeat fault, RX fault")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/qemu/cuty.elf")
