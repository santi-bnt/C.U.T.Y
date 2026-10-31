"""Repository-root launcher shim; all application modules live in raspberry/src/cuty."""

from pathlib import Path

__path__ = [str(Path(__file__).resolve().parent / "raspberry" / "src" / "cuty")]

if __name__ == "__main__":
    from cuty.main import main

    raise SystemExit(main())
