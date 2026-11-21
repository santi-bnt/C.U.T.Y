"""Serialization helpers for the existing experimental STM32 V2 line protocol."""
from enum import Enum
from dataclasses import dataclass


class Axis(str, Enum):
    HEAD_PAN = "HEAD_PAN"
    LEFT_ARM = "LEFT_ARM"
    RIGHT_ARM = "RIGHT_ARM"


def command(line: str) -> bytes:
    """Valida un registro V2 y lo serializa con terminador LF.

    `line` no debe incluir CR/LF. Lanza `ValueError` para comandos legacy,
    campos extra, ejes reservados o posiciones fuera de -1000..1000.
    """
    if not isinstance(line, str) or "\n" in line or "\r" in line:
        raise ValueError("command must be one line without terminator")
    allowed = {"V2,HB", "V2,ARM", "V2,START", "V2,DISARM", "V2,RESET"}
    valid = line in allowed
    fields = line.split(",")
    if len(fields) == 4 and fields[:2] == ["V2", "TARGET"]:
        axis, raw = fields[2:]
        if axis in {a.value for a in Axis} and raw and raw.lstrip("-").isdigit():
            valid = raw != "-" and len(raw.lstrip("-")) <= 4 and -1000 <= int(raw) <= 1000
    if not valid:
        raise ValueError(f"invalid V2 command: {line!r}")
    return (line + "\n").encode("ascii")


def target(axis: Axis | str, milli_units: int) -> bytes:
    """Construye una consigna V2 en milésimas de unidad normalizada."""
    if isinstance(milli_units, bool) or int(milli_units) != milli_units:
        raise ValueError("target must be an integer number of milli-units")
    return command(f"V2,TARGET,{Axis(axis).value},{int(milli_units)}")


@dataclass(frozen=True)
class Response:
    kind: str
    fields: tuple[str, ...]

    @property
    def accepted(self) -> bool | None:
        if self.kind == "ACK":
            return True
        if self.kind == "NACK":
            return False
        return None


def parse_response(line: str) -> Response:
    """Comprueba el prefijo y tipo de respuesta antes de exponer sus campos."""
    fields = line.strip().split(",")
    if len(fields) < 3 or fields[0] != "V2" or fields[1] not in {"ACK", "NACK", "STATE", "TELEM"}:
        raise ValueError(f"invalid V2 response: {line!r}")
    return Response(fields[1], tuple(fields[2:]))
