"""Exercise HDMI/no-HDMI discovery using synthetic Linux sysfs entries."""
import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    'cuty_display', Path(__file__).resolve().parents[1] / 'touchscreen/cuty_display.py')
display = importlib.util.module_from_spec(spec)
spec.loader.exec_module(display)


def framebuffer(root, number, name='fb_ili9486', size='480,320', depth=16, stride=960):
    info = root / 'graphics' / f'fb{number}'
    info.mkdir(parents=True)
    devices = root / 'dev'
    devices.mkdir(exist_ok=True)
    (devices / info.name).touch()
    for key, value in dict(name=name, virtual_size=size, bits_per_pixel=depth, stride=stride).items():
        (info / key).write_text(str(value))
    return devices / info.name, info


@pytest.mark.parametrize('spi_number', [0, 1])
def test_finds_spi_with_or_without_hdmi(tmp_path, spi_number):
    expected = framebuffer(tmp_path, spi_number)
    if spi_number == 1:
        framebuffer(tmp_path, 0, name='vc4drmfb', size='1920,1080', depth=32, stride=7680)
    assert display.find_touchscreen(tmp_path / 'graphics', tmp_path / 'dev') == expected


@pytest.mark.parametrize('changes', [
    {'name': 'vc4drmfb'}, {'depth': 32}, {'size': '320,480'}, {'stride': 1024},
])
def test_rejects_other_displays_and_unsupported_formats(tmp_path, changes):
    framebuffer(tmp_path, 0, **changes)
    with pytest.raises(RuntimeError, match='pantalla SPI'):
        display.find_touchscreen(tmp_path / 'graphics', tmp_path / 'dev')


def test_skips_incomplete_device(tmp_path):
    _, info = framebuffer(tmp_path, 0)
    (info / 'bits_per_pixel').unlink()
    expected = framebuffer(tmp_path, 1)
    assert display.find_touchscreen(tmp_path / 'graphics', tmp_path / 'dev') == expected


def test_waits_for_display_to_appear(monkeypatch):
    attempts = iter([RuntimeError('not ready'), ('/dev/fb0', 'sysfs')])

    def discover():
        result = next(attempts)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(display, 'find_touchscreen', discover)
    monkeypatch.setattr(display.time, 'sleep', lambda seconds: None)
    assert display.wait_for_touchscreen(60) == ('/dev/fb0', 'sysfs')


def test_wait_timeout_reports_missing_screen(monkeypatch):
    def missing():
        raise RuntimeError('pantalla SPI ausente')

    monkeypatch.setattr(display, 'find_touchscreen', missing)
    with pytest.raises(RuntimeError, match='pantalla SPI ausente'):
        display.wait_for_touchscreen(0)
