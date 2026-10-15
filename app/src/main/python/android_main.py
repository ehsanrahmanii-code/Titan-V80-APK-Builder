"""Start the complete TITAN PRO V80 engine inside the TAI Android app."""
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


def _prepare_home(app_files_dir: str | None = None) -> Path:
    """Prepare one writable JJJ data root before importing any TITAN layers."""
    if app_files_dir:
        root = Path(app_files_dir).resolve() / "JJJ"
        root.mkdir(parents=True, exist_ok=True)
        probe = root / ".titan_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        os.environ["TITAN_HOME"] = str(root)
        os.environ["HOME"] = str(Path(app_files_dir).resolve())
        os.environ["ANDROID_PRIVATE"] = str(Path(app_files_dir).resolve())
        return root

    for key in ("ANDROID_PRIVATE", "HOME", "TMPDIR"):
        value = (os.environ.get(key) or "").strip()
        if not value:
            continue
        try:
            root = Path(value) / "JJJ"
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".titan_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            os.environ["TITAN_HOME"] = str(root)
            return root
        except OSError:
            continue
    raise RuntimeError("No writable app-private JJJ storage directory is available.")


def _ensure_path() -> None:
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)


def start_server(app_files_dir: str | None = None) -> None:
    global _started, _server_error
    with _lock:
        if _started:
            return
        _started = True

    try:
        _prepare_home(app_files_dir)
        _ensure_path()

        os.environ.setdefault("TITAN_HOST", "127.0.0.1")
        os.environ.setdefault("TITAN_PORT", "5000")
        os.environ.setdefault("TITAN_OPEN_BROWSER", "0")
        os.environ.setdefault("TITAN_DEBUG", "0")
        os.environ["TITAN_ANALYSIS_ONLY"] = "1"
        os.environ["TITAN_LIVE_TRADING"] = "0"
        os.environ.pop("TITAN_LIVE_UNLOCK", None)

        from titan.runtime import load

        ns = load(__file__, as_main=False, stop_before="entry/main_entry")
        app = ns.get("app")
        if app is None:
            raise RuntimeError("Flask dashboard app was not created by TITAN V80 layers")

        ns["HOST"] = "127.0.0.1"
        ns["PORT"] = 5000

        def run() -> None:
            global _server_error
            try:
                app.run(host="127.0.0.1", port=5000, debug=False,
                        use_reloader=False, threaded=True)
            except Exception as exc:
                _server_error = f"{type(exc).__name__}: {exc}"
                traceback.print_exc()

        threading.Thread(target=run, name="tai-titan-v80-server", daemon=True).start()
        # Give Flask's listener time to bind; MainActivity also checks readiness.
        time.sleep(1.0)

        for name in ("start_live_engine", "_v29_auto_loop"):
            fn = ns.get(name)
            if callable(fn):
                try:
                    if name == "start_live_engine":
                        fn()
                    else:
                        threading.Thread(target=fn, name=name, daemon=True).start()
                except Exception:
                    traceback.print_exc()

    except Exception as exc:
        with _lock:
            _started = False
        _server_error = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
        raise


def get_status() -> dict:
    return {"started": _started, "error": _server_error,
            "home": os.environ.get("TITAN_HOME")}
