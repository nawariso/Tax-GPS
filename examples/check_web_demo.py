"""Run frontend lifecycle regression tests against an isolated real-engine server.

Usage: uv run python -m examples.check_web_demo
Requires Node.js with its built-in test runner and fetch (Node 22+).
"""

from __future__ import annotations

import os
import shutil
import subprocess
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from examples.web_demo import DemoHandler


def main() -> int:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js 22+ is required for frontend lifecycle verification")
    test_file = Path(__file__).parents[1] / "tests" / "web" / "test_app.cjs"
    with ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler) as server:
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            result = subprocess.run(  # noqa: S603 - fixed repository test, no caller command
                [node, "--test", str(test_file)],
                env={**os.environ, "TAX_GPS_DEMO_URL": f"http://127.0.0.1:{server.server_port}"},
                check=False,
                timeout=30,
            )
            return result.returncode
        finally:
            server.shutdown()
            thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
