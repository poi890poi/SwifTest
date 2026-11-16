"""Compact reference for observing departure from a known screen."""

from dataclasses import dataclass
import math

import cv2
import numpy as np


def thumbnail(image):
    # Each cell is a spatial average, which attenuates noise and small movements.
    height, width = image.shape[:2]
    if height >= 64 and width >= 96 and height % 2 == 0 and width % 2 == 0:
        # OpenCV has an efficient 2x2 area-average path for even-sized frames.
        image = cv2.resize(image, (width // 2, height // 2), interpolation=cv2.INTER_AREA)
    return cv2.resize(image, (48, 32), interpolation=cv2.INTER_AREA)


@dataclass(frozen=True)
class ScreenSignature:
    geometry: tuple
    colors: bytes
    stable: bytes

    @classmethod
    def capture(cls, frames):
        first = next(frames)
        geometry = first.shape
        colors = thumbnail(first)
        low, high = colors.copy(), colors.copy()
        for frame in frames:
            if frame.shape != geometry:
                raise ValueError("Display geometry changed while sampling the reference screen.")
            sample = thumbnail(frame)
            np.minimum(low, sample, out=low)
            np.maximum(high, sample, out=high)
        stable = (high - low).max(axis=2) < 24
        if stable.mean() < 0.25:
            raise ValueError("Too little of the reference screen stayed stable across the samples.")
        return cls(geometry, colors.tobytes(), stable.tobytes())

    def changed_fraction(self, frame):
        if frame.shape != self.geometry:
            raise ValueError("Display geometry changed since the reference screen was captured.")
        sample = thumbnail(frame)
        reference = np.frombuffer(self.colors, dtype=np.uint8).reshape(sample.shape)
        stable = np.frombuffer(self.stable, dtype=np.bool_).reshape(sample.shape[:2])
        changed = cv2.absdiff(reference, sample).max(axis=2) >= 24
        return np.count_nonzero(changed & stable) / np.count_nonzero(stable)


def validate_change_options(min_fraction=0.35, persist=0.2):
    if not math.isfinite(min_fraction) or not 0 < min_fraction <= 1:
        raise ValueError("min_fraction must be greater than zero and at most one.")
    if not math.isfinite(persist) or persist < 0:
        raise ValueError("persist must be finite and nonnegative.")
