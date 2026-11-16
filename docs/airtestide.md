# Edit SwifTest image scripts in AirtestIDE

The [Loading.air example](../examples/airtestide/Loading.air/Loading.py) runs
against the local SwifTest Android fixture. The fixture displays the exact
40 × 36 pixel PNG shown here. Tap the symbol to finish loading after a short
delay. A small spinner animates while the surrounding screen stays stable.

![SwifTest fixture start button](../examples/airtestide/Loading.air/start.png)

From the repository root, build and install the fixture on your test device.
Use the same device serial for installation and execution.

```text
python tests/android_variants_fixture/build.py --sdk PATH_TO_ANDROID_SDK
adb -s SERIAL install -r artifacts/androidtestkit/variants-fixture/fixture.apk
python -m swiftest run examples/airtestide/Loading.air --serial SERIAL
```

The script launches the fixture, samples the old screen, taps the symbol and
waits for the background to change. The runner reports the outcome without
needing a template for the destination.

Install AirtestIDE separately from NetEase and open `Loading.air` to edit
the script. [AirtestIDE download and terms](https://airtest.netease.com/download.html)

AirtestIDE represents a captured image as a literal `Template(...)` expression
and provides an image/code toggle and a picture editor. [Airtest image scripts](https://airtest.doc.io.netease.com/en/IDEdocs/airtest_framework/3_airtest_image/)

For your own project, create `Load.air/Load.py`, keep captured PNGs in
`Load.air/`, and use these imports in place of the default Airtest header.
Use AirtestIDE's screenshot control to insert your own template, then save.

```python
from swiftest import screen_signature, touch, wait_screen_change
from swiftest.compat import Template

before = screen_signature()
touch(Template(r"tpl123.png", record_pos=(0.1, 0.2), resolution=(1080, 2400)))
wait_screen_change(before, timeout=30)
```

Run the saved project with the Python environment where SwifTest is installed.
The CLI creates the session and resolves the PNG relative to the entry point.

```text
python -m swiftest run Load.air --serial YOUR_DEVICE_SERIAL
```

The recorded-template constructor supports `filename`, `threshold`, `target_pos`,
`record_pos`, `resolution` and `rgb`. Positions 0 and 5 select the center.
Recorded resolution supplies a scale hint. SwifTest's native `touch` still
requires a unique match and accepts `expect=`. The Airtest-specific multiscale
options `scale_max` and `scale_step` are unsupported. For native SwifTest
regions, masks or explicit scales use `swiftest.Template`.

AirtestIDE's Play button uses its configured runner. The workflow verified here
is editing the literal in a standard project layout and executing the saved
file with the SwifTest CLI. For scripts that retain `from airtest.core.api
import *`, use `swiftest convert` to produce a separate SwifTest project.

Conversion copies referenced images or project assets. Review their redistribution rights before sharing a converted project.
