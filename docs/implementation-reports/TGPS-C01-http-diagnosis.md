# C01 HTTP F09 diagnosis — 2026-10-15

Status: **investigation completed; original WinError 10053 OPEN / not reproduced**.
This is not an unconditional acceptance or proof that the intermittent failure is fixed.

Hypothesis: rejecting a POST before reading its body leaves unread bytes on the Windows
socket; closing that connection may lose the response. The historical handler leaves a
bounded body unread; the current handler drains only known-size, non-transfer-encoded
bodies up to MAX_BODY with a 0.25s timeout and explicitly sends Connection: close.
Host/Origin, framing, size and private-file rejection remain enabled.

Comparison: archived Git commit `de85aee67e3da34e6a83c296ad88d6e377f0858a`, extracted
under ignored tmp without changing HEAD or swapping working files, versus current C01.
Both delivered 100/100 full 403 JSON responses. Historical handler left 100 unread `{}`
bodies; current handler drained 100. Elapsed 0.565s / 0.454s. Thus the lifecycle defect
is demonstrated, but neither run reproduces the historical transport exception.

The existing narrow regression
`tests/acceptance/test_web_demo.py::test_rejected_post_consumes_its_bounded_body_before_connection_close`
asserts no unread body. Against the measured historical handler that assertion would fail
(`{}` instead of empty bytes); current regression passed ten consecutive runs. This
session did not write or claim an original RED→GREEN for the already-existing HTTP fix.
Repeated full suite passed (685 tests). Full raw results and actual runtime strings are
retained in [JSON evidence](TGPS-C01-http-evidence.json). Final quality/coverage results
are recorded separately in [implementation report](TGPS-C01.md).

Re-run targeted regression with a fresh server (the pytest fixture binds port 0):

```powershell
1..10 | ForEach-Object {
    uv run --locked pytest tests/acceptance/test_web_demo.py -k rejected_post -q
    if ($LASTEXITCODE -ne 0) { throw 'HTTP regression failed' }
}
uv run --locked pytest -q
uv run --locked python -m examples.check_web_demo
```

For the old/current socket comparison and matching historical tax replay, recreate
the following two scratch scripts under `tmp` and run `uv run --locked python tmp/c01_diagnose.py`.
The scripts are diagnostic tooling only, use synthetic data and real loopback sockets,
and do not enter the deterministic calculation path. They retain the original Git
commit as the historical engine artifact; no compatibility engine is invented.
They require running from the repository root with the uv environment already synced.

`tmp/c01_probe.py`:

```python
"""Offline Windows socket diagnosis using synthetic bodies only."""

import json
import platform
import sys
import time
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Event, Thread

root = Path(sys.argv[1]).resolve()
sys.path[:0] = [str(root / "src"), str(root)]
from examples.web_demo import DemoHandler
from tax_gps.audit import create_audit_snapshot, replay
from tax_gps.core.money import Money
from tax_gps.core.tax_year import TaxYear
from tax_gps.engine import ENGINE_VERSION, calculate_tax
from tax_gps.opportunity.loader import load_bundled_catalog
from tax_gps.policy.activation import activate_rule_pack
from tax_gps.policy.loader import load_bundled_rule_pack
from tax_gps.profile.models import ExistingTaxBenefits, IncomeProfile, UserProfile

pack = activate_rule_pack(load_bundled_rule_pack())
profile = UserProfile(
    "history-probe",
    "1",
    TaxYear(2026),
    IncomeProfile(Money.of(990500)),
    ExistingTaxBenefits(social_security_paid=Money.of(10500)),
)
state = calculate_tax(profile, pack)
snapshot = create_audit_snapshot(profile, state, pack)
assert replay(snapshot, profile, pack) == state

observed = []
finished = Event()


class ProbeHandler(DemoHandler):
    def do_POST(self):
        super().do_POST()
        self.connection.settimeout(0.1)
        try:
            observed.append(self.rfile.read(2).decode())
        except OSError:
            observed.append("")
        finally:
            finished.set()


started = time.perf_counter()
errors = []
with ThreadingHTTPServer(("127.0.0.1", 0), ProbeHandler) as server:
    thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
    thread.start()
    try:
        for i in range(100):
            finished.clear()
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            try:
                connection.request(
                    "POST",
                    "/api/calculate",
                    "{}",
                    {"Origin": "https://untrusted.example"},
                )
                response = connection.getresponse()
                assert response.status == 403
                assert json.loads(response.read())["error"]
            except Exception as exc:
                errors.append({"iteration": i, "type": type(exc).__name__, "error": str(exc)})
            finally:
                connection.close()
                assert finished.wait(2)
    finally:
        server.shutdown()
        thread.join(5)

print(
    json.dumps(
        {
            "runtime": sys.version,
            "platform": platform.platform(),
            "engine": ENGINE_VERSION,
            "pack": pack.version,
            "catalog": load_bundled_catalog().version,
            "pit": state.pit.canonical() if state.pit is not None else None,
            "replay_output_hash": snapshot.output_hash,
            "requests": 100,
            "errors": errors,
            "unread_bodies": observed.count("{}"),
            "drained_bodies": observed.count(""),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        },
        indent=2,
    )
)
```

`tmp/c01_diagnose.py`:

```python
"""Extract a historical Git artifact to ignored scratch; preserve working files."""

import io
import subprocess
import sys
import zipfile
from pathlib import Path

root = Path.cwd()
history = root / "tmp" / "c01-history"
archive = subprocess.check_output(
    ["git", "archive", "--format=zip", "de85aee67e3da34e6a83c296ad88d6e377f0858a"]
)
with zipfile.ZipFile(io.BytesIO(archive)) as files:
    for entry in files.infolist():
        target = (history / entry.filename).resolve()
        assert target.is_relative_to(history.resolve())
    files.extractall(history)
for label, source in (("historical", history), ("current", root)):
    result = subprocess.run(
        [sys.executable, str(root / "tmp" / "c01_probe.py"), str(source)],
        cwd=source,
        text=True,
        capture_output=True,
        check=True,
    )
    (root / "tmp" / f"c01-{label}-probe.json").write_text(result.stdout, encoding="utf-8")
    print(label, result.stdout)
```
