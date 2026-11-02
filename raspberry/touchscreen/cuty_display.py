"""Locate the SPI touchscreen independently of HDMI framebuffer numbering."""
import argparse
from pathlib import Path
import time


def find_touchscreen(graphics=Path('/sys/class/graphics'), devices=Path('/dev')):
    """Return the supported ILI9486 display, never an HDMI framebuffer."""
    for info in sorted(graphics.glob('fb[0-9]*')):
        device = devices / info.name
        try:
            name = (info / 'name').read_text().strip()
            size = (info / 'virtual_size').read_text().strip()
            depth = int((info / 'bits_per_pixel').read_text())
            stride = int((info / 'stride').read_text())
        except (OSError, ValueError):
            continue
        if (device.exists() and name == 'fb_ili9486' and size == '480,320'
                and depth == 16 and stride == 960):
            return device, info
    raise RuntimeError('No aparece la pantalla SPI fb_ili9486 de 480x320 RGB565; comprueba waveshare35a.')


def wait_for_touchscreen(seconds):
    deadline = time.monotonic() + seconds
    while True:
        try:
            return find_touchscreen()
        except RuntimeError:
            if time.monotonic() >= deadline:
                raise
            time.sleep(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--wait', type=float, default=0)
    args = parser.parse_args()
    try:
        device, _ = wait_for_touchscreen(args.wait)
    except RuntimeError as error:
        raise SystemExit(str(error))
    print(f'Pantalla C.U.T.Y: {device}', flush=True)
