# SwifTest

**Write intent. Run fast.**

SwifTest is a standalone Python library and command-line runner for Android games
and apps. Put image crops beside a Python script, then write the actions:

```python
from swiftest import open_app, touch

open_app("com.example.app")
touch("play.png")
touch("confirm.png", expect="ready.png")
```

Replace the package and PNGs with your app and its cropped controls. Run with
`swiftest run test_game.py --serial YOUR_DEVICE_SERIAL`. Image paths are relative
to the script. SwifTest waits, finds a unique match, taps and checks `expect`.
No catalog, profile, OCR or session setup is required for an image script.

For a complete example with actual PNGs, see the
[Genshin script and template gallery](examples/genshin/README.md).
`Template(...)` adds options such as regions, scales and masks. Named catalogs,
rendered text, native selectors and explicit checkpoints remain available when needed.

## Start here

- [Documentation index](docs/index.md)
- [Installation, selectors, scripts and reports](docs/android-usage.md)
- [API and build reference](docs/swiftest.md)
- [Framework requirements and limits](docs/android-requirements.md)
- [Copyable starter project](examples/starter/README.md)

## Install and run

Use Python 3.9 or newer and Android SDK Platform Tools. Enable USB debugging and
authorize the computer on the phone. Clone this repository, then install from it:

```text
git clone git@github.com:poi890poi/SwifTest.git
cd SwifTest
python -m pip install .
python -m swiftest devices
python -m swiftest run path/to/test_game.py --serial YOUR_DEVICE_SERIAL
```

Install `.[ocr]` for local rendered-text recognition. Use `.[ocr-fast]` for the optional
OpenVINO CPU adapter, or `.[scrcpy]` for streaming capture. Template-only use needs
no OCR extra. This repository and its source archives contain the documentation,
examples, tests and build script; no AriaTrace checkout is needed.

## Build and test

```text
python -m pip install "setuptools>=61" wheel
python scripts/build_swiftest.py
python -m unittest discover -s tests -p "test_swiftest*.py"
python -m unittest discover -s tests -p "test_genshin*.py"
```

The build writes a wheel, a complete source archive and `SHA256SUMS.txt` to
`dist/`. It builds the wheel from the source archive and checks packaged source
and the Android capture helper. `--output PATH` changes the output directory.
Build prerequisites and runtime dependencies are ordinary Python packages.

CI builds and installs the wheel on Windows, Linux and macOS. Live hardware
qualification remains device-specific. Package documentation is available in
this repository and the source archive; the wheel contains the runtime and its
package description.

## What is included

| Directory | Purpose |
| --- | --- |
| `swiftest/` | Runtime library and CLI |
| `docs/` | Usage, API, requirements and concise research findings |
| `examples/` | Starter, Settings, visual game and configured-variant examples |
| `tests/` | Offline contracts and optional Android fixture source |
| `scripts/` | Standalone package builder |
| `benchmarks/android/` | Optional experiment source and reproduction notes |

Exact-region caching helps when relevant pixels stay unchanged. Animation within
a region still needs evaluation. Streaming supplies frame notifications, not
semantic game events. Regional OCR can change recognition and can be slower with
some scaling settings. See the [measured results and limits](docs/android-visual-evaluation-2026-11-07.md).

The six small PNGs in `examples/genshin/assets/` are shipped example inputs.
Historical benchmark artifacts, full-screen captures, copied dependencies and
device recordings are not included. They are not installation or test requirements.
See [project origin](docs/origin.md) for the source provenance.
