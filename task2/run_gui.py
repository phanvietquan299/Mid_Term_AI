import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent))
from midterm_gui.app_window import main as gui_main


def main():
    gui_main()


if __name__ == "__main__":
    main()
