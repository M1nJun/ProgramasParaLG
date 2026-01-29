from __future__ import annotations

def main() -> None:
    from mavin_fetcher_gui.app import main as gui_main
    raise SystemExit(gui_main())

if __name__ == "__main__":
    main()
