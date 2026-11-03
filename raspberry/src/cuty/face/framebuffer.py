"""Fast RGB565 output for the SPI framebuffer.

The touchscreen's per-pixel Python loop is fine for menus but far too slow for
animation. Here the conversion is vectorised with NumPy and only the rows
that changed since the previous frame are written. With ``mmap`` the fbtft
driver's deferred I/O then refreshes just that band of the panel, which is
what keeps the eyes smooth over SPI.
"""

from __future__ import annotations

import mmap
import os
from pathlib import Path

import numpy as np
from PIL import Image


def to_rgb565(image: Image.Image) -> np.ndarray:
    """RGB image -> (H, W) little-endian uint16 array in RGB565."""
    rgb = np.asarray(image.convert("RGB"), dtype=np.uint16)
    packed = ((rgb[..., 0] >> 3) << 11) | ((rgb[..., 1] >> 2) << 5) | (rgb[..., 2] >> 3)
    return packed.astype("<u2")


class FramebufferWriter:
    """Writes frames to a 16-bit framebuffer, skipping rows that did not change."""

    def __init__(self, path: str | os.PathLike, width: int, height: int) -> None:
        self.path = Path(path)
        self.width, self.height = width, height
        self._size = width * height * 2
        self._fd = os.open(self.path, os.O_RDWR)
        try:
            self._map: mmap.mmap | None = mmap.mmap(self._fd, self._size, access=mmap.ACCESS_WRITE)
        except (OSError, ValueError):
            self._map = None  # Fall back to seek + write.
        self._previous: np.ndarray | None = None

    def invalidate(self) -> None:
        """Forget the last frame, e.g. after another screen drew over it."""
        self._previous = None

    def write(self, frame: np.ndarray) -> tuple[int, int] | None:
        """Write a (H, W) RGB565 frame; return the (first, end) rows written."""
        if frame.shape != (self.height, self.width):
            raise ValueError(f"Frame must be {self.height}x{self.width}, got {frame.shape}")
        if self._previous is None:
            first, end = 0, self.height
        else:
            changed = np.flatnonzero((frame != self._previous).any(axis=1))
            if changed.size == 0:
                return None
            first, end = int(changed[0]), int(changed[-1]) + 1
        data = frame[first:end].tobytes()
        offset = first * self.width * 2
        if self._map is not None:
            self._map[offset:offset + len(data)] = data
        else:
            os.pwrite(self._fd, data, offset)
        self._previous = frame.copy()
        return first, end

    def close(self) -> None:
        if self._map is not None:
            self._map.close()
            self._map = None
        if self._fd >= 0:
            os.close(self._fd)
            self._fd = -1

    def __enter__(self) -> FramebufferWriter:
        return self

    def __exit__(self, *exc) -> None:
        self.close()
