"""Start TITAN PRO V80 modular server inside Chaquopy."""
from __future__ import annotations

import os
import sys
import threading
import time
import traceback
from pathlib import Path

_started = False
_lock = threading.Lock()
_server_error = None


def _prepare_home() -> Path:
    candidates = []
    for key in ("HOME", "TMPDIR", "ANDROID_PRIVATE"):
        v = (os.environ.get(key) or "").strip()
        if v:
            candidates.append(Path(v) / "TITAN_V80")
    candidates.extend([
        Path("/storage/emulated/0/TITAN_V80"),
        Path("/sdcard/TITAN_V80"),
        Path.home() / "TITAN_V80",
        Path("/data/data/org.titanv80.app/files/TITAN_V80"),
    ])
    for c in candidates:
        try:
            c.mkdir(parents=True, exist_ok=True)
            probe = c / ".w"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            os.environ["TITAN_HOME"] = str(c)
            os.environ["HOME"] = str(c.parent)
            return c
        except Exception:
            continue
    fallback = Path("/data/data/org.titanv80.app/files/TITAN_V80")
    try:
        fallback.mkdir(parents=True, exist_ok=True)
        os.environ["TITAN_HOME"] = str(fallback)
    except Exception:
        pass
    return fallback


def _ensure_path() -> None:
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def start_server() -> None:
    global _started, _server_error
    with _lock:
        if _started:
            return
        _started = True

    try:
        _prepare_home()
        _ensure_path()

        os.environ.setdefault("TITAN_HOST", "127.0.0.1")
        os.environ.setdefault("TITAN_PORT", "5000")
        os.environ.setdefault("TITAN_OPEN_BROWSER", "0")
        os.environ.setdefault("TITAN_DEBUG", "0")
        os.environ.setdefault("TITAN_ANALYSIS_ONLY", "1")
        os.environ.setdefault("TITAN_LIVE_TRADING", "0")

        from titan.runtime import load

        ns = load(__file__, as_main=False, stop_before="entry/main_entry")

        app = ns.get("app")
        if app is None:
            raise RuntimeError("Flask app not found after loading V80 layers")

        ns["HOST"] = "127.0.0.1"
        ns["PORT"] = 5000

        def run():
            try:
                app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False, threaded=True)
            except Exception as exc:
                global _server_error
                _server_error = f"{type(exc).__name__}: {exc}"
                traceback.print_exc()

        threading.Thread(target=run, name="titan-v80", daemon=True).start()
        time.sleep(1.5)

        # optional background workers
        for name in ("start_live_engine", "_v29_auto_loop"):
            fn = ns.get(name)
            if callable(fn):
                try:
                    if name == "start_live_engine":
                        fn()
                    else:
                        threading.Thread(target=fn, name=name, daemon=True).start()
                except Exception:
                    pass

    except Exception as exc:
        _server_error = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
        raise


def get_status():
    return {"started": _started, "error": _server_error, "home": os.environ.get("TITAN_HOME")}
