"""Perfil confirmado de calibración mecánica requerido para modo robot."""
from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

AXIS_PINS = {"HEAD_PAN": "PB6/J7", "LEFT_ARM": "PB7/J8", "RIGHT_ARM": "PB8/J9"}


@dataclass(frozen=True)
class AxisCalibration:
    axis: str
    pin: str
    min_us: int
    center_us: int
    max_us: int
    reverse: bool
    max_velocity_per_s: float
    max_acceleration_per_s2: float
    mechanical_calibration_confirmed: bool
    joint_mapping_confirmed: bool

    def validate(self) -> None:
        if self.axis not in AXIS_PINS or self.pin != AXIS_PINS[self.axis]:
            raise ValueError("El eje no coincide con un canal servo reservado conocido")
        pulses = (self.min_us, self.center_us, self.max_us)
        if any(isinstance(value, bool) or not isinstance(value, int) for value in pulses):
            raise ValueError("Los límites PWM deben ser enteros en microsegundos")
        if not (1000 <= self.min_us < self.center_us < self.max_us <= 2000):
            raise ValueError("Se requiere min < centro < max dentro de 1000..2000 us")
        if not isinstance(self.reverse, bool):
            raise ValueError("reverse debe ser booleano")
        if any(not math.isfinite(value) or value <= 0 for value in (
            self.max_velocity_per_s, self.max_acceleration_per_s2,
        )):
            raise ValueError("Velocidad y aceleración deben ser positivas y finitas")
        if self.mechanical_calibration_confirmed is not True or self.joint_mapping_confirmed is not True:
            raise ValueError("Falta confirmación explícita de calibración o mapeo")


@dataclass(frozen=True)
class RobotCalibration:
    axes: tuple[AxisCalibration, ...]

    def validate_complete(self) -> None:
        by_axis = {axis.axis: axis for axis in self.axes}
        if len(by_axis) != len(self.axes) or set(by_axis) != set(AXIS_PINS):
            raise ValueError("El perfil debe contener exactamente los tres ejes, una vez cada uno")
        for axis in self.axes:
            axis.validate()

    @classmethod
    def load(cls, path: str | Path) -> "RobotCalibration":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(data, dict) or set(data) != {"schema", "axes"} or data["schema"] != 1:
            raise ValueError("Formato de perfil de calibración no reconocido")
        if not isinstance(data["axes"], list):
            raise ValueError("axes debe ser una lista")
        required = {
            "axis", "pin", "min_us", "center_us", "max_us", "reverse",
            "max_velocity_per_s", "max_acceleration_per_s2",
            "mechanical_calibration_confirmed", "joint_mapping_confirmed",
        }
        axes = []
        for item in data["axes"]:
            if not isinstance(item, dict) or set(item) != required:
                raise ValueError("Cada eje debe incluir todos y solo los campos del esquema")
            axes.append(AxisCalibration(**item))
        profile = cls(tuple(axes))
        profile.validate_complete()
        return profile
