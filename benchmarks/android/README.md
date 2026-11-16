# Android benchmarks

Build and install the [SwifTest Android fixture](../../docs/airtestide.md).
The latency probe measures repeated input against the fixture's native counter.
It checks the result on the device after each input and saves per-trial timing.

```text
python benchmarks/android/latency_fixture.py --serial SERIAL --rounds 6 --capture --output artifacts/fixture-latency
```

The [loading-screen example](../../docs/airtestide.md) exercises image matching
and departure detection on an animated screen. To measure matching and caching
offline with generated frames, run the visual evaluation probe.

```text
python benchmarks/android/visual_evaluation_probe.py --source-root . --seed 17 --output artifacts/visual-evaluation.json
```

## Historical measurements

The [November 7 comparison](../../docs/android-airtest-current-comparison-2026-11-07.md)
measured the separately installed Airtest 1.4.3 **Python library** on one Samsung
SM-G781B running Android 13. Its results apply to the documented versions,
workloads, capture methods and polling settings. AirtestIDE and AirLab were
outside that comparison. SwifTest is independent of NetEase. [Library license](https://github.com/AirtestProject/Airtest/blob/master/LICENSE) · [Editor and service terms](https://airtest.netease.com/download.html)
