import sys
from pathlib import Path

def main():
    if "--smoke-ui" in sys.argv:
        import os
        os.environ["QT_QPA_PLATFORM"] = "offscreen"
        from PySide6.QtWidgets import QApplication
        from PySide6.QtGui import QFontDatabase, QFont
        from .ui import STYLE, assets_root
        from tools.gui_integration import run
        app = QApplication([])
        app.setStyle("Fusion")
        QFontDatabase.addApplicationFont(str(assets_root() / "Inter.ttf"))
        app.setFont(QFont("Inter", 10))
        app.setStyleSheet(STYLE)
        run(app, sys.argv[sys.argv.index("--smoke-ui") + 1])
        return 0
    if "--worker" in sys.argv:
        from .engine import worker
        return worker(sys.argv[sys.argv.index("--worker") + 1])
    if "--verify" in sys.argv:
        # This exercises the same engine and exporters used by the GUI.
        import argparse, json, uuid
        parser = argparse.ArgumentParser()
        parser.add_argument("--verify", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--model-root")
        parser.add_argument("--language", default="de")
        parser.add_argument("--speaker-count", type=int, default=2)
        parser.add_argument("--no-speakers", action="store_true")
        parser.add_argument("--block-network", action="store_true")
        args = parser.parse_args()
        if args.block_network:
            import socket
            def blocked(*_args, **_kwargs):
                raise RuntimeError("Network access forbidden during offline verification")
            socket.socket.connect = blocked
            socket.create_connection = blocked
            socket.getaddrinfo = blocked
        from .ui import app_root
        from .engine import run_job
        job = {"id": uuid.uuid4().hex, "files": [args.verify], "output": args.output, "models": args.model_root or str(app_root() / "models"), "options": {"language": args.language, "speakers": not args.no_speakers, "speaker_count": args.speaker_count, "ui_language": "de"}}
        run_job(job)
        return 0
    from .ui import launch
    return launch()

if __name__ == "__main__":
    raise SystemExit(main())
