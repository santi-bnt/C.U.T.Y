#!/usr/bin/env python3
"""Sample C.U.T.Y. Linux process CPU/RSS while the robot is running.

This utility deliberately does not open the camera or audio devices. Run it on
the Pi alongside cuty-launcher.service; camera-stage timings come from the
FaceTracker's [VISION PERF] journal entries.
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path


def read_process(pid: int) -> tuple[str, int, int] | None:
    base = Path("/proc") / str(pid)
    try:
        stat = (base / "stat").read_text()
        # comm may contain spaces; fields after the final ')' start at field 3.
        fields = stat[stat.rfind(")") + 2:].split()
        cpu_ticks = int(fields[11]) + int(fields[12])  # utime + stime
        rss_pages = int(fields[21])
        cmd = (base / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
        if not cmd:
            return None
        return cmd, cpu_ticks, rss_pages * os.sysconf("SC_PAGE_SIZE")
    except (OSError, ValueError, IndexError):
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=300, help="sample duration seconds (default 300)")
    parser.add_argument("--interval", type=float, default=1, help="sample interval seconds (default 1)")
    parser.add_argument("--csv", type=Path, default=Path("cuty-vision-benchmark.csv"))
    args = parser.parse_args()
    if args.duration <= 0 or args.interval <= 0:
        parser.error("duration and interval must be positive")
    if not sys.platform.startswith("linux") or not Path("/proc/stat").exists():
        parser.error("run this script on the Raspberry Pi/Linux robot")

    clk_tck = os.sysconf("SC_CLK_TCK")
    previous: dict[int, tuple[int, float]] = {}
    deadline = time.monotonic() + args.duration
    samples = []
    with args.csv.open("w", newline="", encoding="utf-8") as output:
        writer = csv.writer(output)
        writer.writerow(("monotonic_s", "pid", "role", "cpu_percent_one_core", "rss_mib"))
        while time.monotonic() < deadline:
            sample_time = time.monotonic()
            for entry in Path("/proc").iterdir():
                if not entry.name.isdigit():
                    continue
                pid = int(entry.name)
                result = read_process(pid)
                if result is None:
                    continue
                cmd, ticks, rss_bytes = result
                lowered = cmd.lower()
                if "cuty" not in lowered and "cuty_launcher.py" not in lowered:
                    continue
                before = previous.get(pid)
                cpu = 0.0 if before is None else max(0.0, (ticks - before[0]) / clk_tck /
                                                     max(0.001, sample_time - before[1]) * 100)
                previous[pid] = (ticks, sample_time)
                role = "launcher/vision" if "cuty_launcher.py" in lowered else "voice/other"
                rss_mib = rss_bytes / (1024 * 1024)
                writer.writerow((f"{sample_time:.3f}", pid, role, f"{cpu:.1f}", f"{rss_mib:.1f}"))
                samples.append((cpu, rss_mib))
            output.flush()
            time.sleep(min(args.interval, max(0, deadline - time.monotonic())))

    if not samples:
        print("No se encontraron procesos C.U.T.Y.; revisa que el launcher esté activo.")
        return 2
    max_cpu = max(item[0] for item in samples)
    max_rss = max(item[1] for item in samples)
    mean_cpu = sum(item[0] for item in samples) / len(samples)
    print(f"Muestras de procesos: {len(samples)}")
    print(f"CPU media (un núcleo): {mean_cpu:.1f}%; pico muestreado: {max_cpu:.1f}%")
    print(f"RSS máximo por proceso: {max_rss:.1f} MiB")
    print(f"CSV: {args.csv.resolve()}")
    print("Estos valores no incluyen memoria/carga de kernel ni atribuyen la carga a cámara vs. modelos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
