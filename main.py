"""Backward-compatible launcher for the Serial Port Assistant."""

from src.app import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
