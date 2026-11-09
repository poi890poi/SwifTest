# Standalone project origin

SwifTest was extracted from `poi890poi/aria-trace` on November 9, 2026, starting
at commit `7b35432b3948590beb02b3291114beebd322175e`. The source repository contains
the earlier implementation and research history. This repository starts with a
focused import of the framework, its examples, tests, documentation and experiment
source, rather than the unrelated PC tracking application.

The runtime modules and Android helper retain their behavior. The standalone
changes provide a project README, a documentation index, source packages that
carry the complete documentation and build/test inputs, and independent CI.
No source import or runtime path requires an AriaTrace installation.

Generated datasets, screenshots, telemetry, cached dependencies, model weights
and local environments were not imported. Dated research notes retain their
original names, paths and hashes as provenance, not as a claim that those files
are in this repository. The optional benchmarks may need their separately held
private inputs; installing, building and running the offline contracts do not.
