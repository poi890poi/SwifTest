# SwifTest purpose and requirements review

Reviewed November 9, 2026 against the repository documentation and our
conversation, with the user's later corrections taking precedence. Implementation
status was checked at source revision `43a46d1`; Airtest's official documentation
and source provide comparison evidence, not SwifTest requirements. Images are
not requirements sources. The review below records the baseline; the implementation
follow-up at the end records which gaps were subsequently closed.

## Purpose and authoring boundary

Build an independent, reusable Android automation framework that makes game
tests easier to write and maintain than Airtest, responds with as little delay
as a human operator, and reduces unnecessary processing, data transfer and power
use. Genshin launch and teleport is an acceptance example, not the product scope.

The user's original definition was: "User script should contain only intent
(UI element position or template). The lib needs to handle trivial things like
wait or retry." The latest clarification is that ordinary Python is appropriate:
the script contains information about game operations. Natural-language parsing,
a VLM and a separate app-specific setup are not required solutions.

| Information in the test | Work owned by the framework |
| --- | --- |
| Launch this package; press Start; open the map; choose this waypoint; teleport | Device setup, observations and input dispatch |
| Identify the target by image, text or position | Target search, OCR where useful, observation reuse and recognition scheduling |
| Expected area, size, scale, relative position, parent dialog, mask and touch offset | Coordinate transforms and enforcing those constraints before input |
| Expected result, meaningful alternatives and allowed game interactions | Readiness, transition verification, bounded waits and safe retries |
| Which operation is optional or may safely repeat | Executing that policy without user-written polling, counters or recovery loops |

Game operations still need to be specified. Pressing Start is a game operation;
polling for Start in a `while` loop is runtime orchestration. A script is not
required to have exactly four statements. Launching a process does not by itself
mean that the game has reached gameplay. The library must derive execution from
the supplied operations and UI facts without requiring a per-game procedural
profile. Moving the same loop into a Genshin helper would not meet the requirement.

## Requirements from the docs and conversation

The [framework requirements](android-requirements.md), [API documentation](swiftest.md)
and conversation establish the following requirements for an independent
Airtest replacement:

1. Familiar compatible interfaces and an Airtest script conversion tool.
2. Limited search regions and scale ranges; expected position and size must
   constrain acceptance, not merely influence a similarity score.
3. Binary masks to exclude changing backgrounds.
4. Configurable strict or relaxed image thresholds.
5. Native normalized screen coordinates from `(0, 0)` to `(1, 1)`.
6. Native touch retry support, with assertive and non-assertive options.
7. Touch offsets from a recognized target.
8. User-selectable ADB or scrcpy image acquisition.
9. Dialog structure awareness, such as locating Close at the top right of a
   detected dialog instead of recognizing an isolated button.
10. A project name; the later explicit choice is **SwifTest**.

Later instructions add or clarify:

- A complete standalone framework for Android tests, with its own repository,
  documentation, tests and pip build. Portable Python workflows.
- Only game-operation information in ordinary scripts; no required app profile,
  catalog, natural-language interpreter or separate procedural setup.
- Content and geometry awareness, including relations between UI elements;
  support text, button and pop-up variants and changes in loading duration.
- Local CPU operation: no VLM, cloud billing/API-key dependency or GPU solution.
- Games must work from rendered pixels without a UI tree. Poco does not solve
  this use case. Native selectors can remain useful for other Android apps.
- Reduce capture, transfer, recognition and input overhead. The responsiveness
  target concerns automation-added delay, excluding time the game itself needs
  to start, load or download. Human-speed operation remains a target to validate.
- Energy awareness: less unnecessary data and work, with time and temperature
  comparisons. Fewer bytes alone do not prove lower energy consumption.
- Improve observation scheduling beyond repeated blocking searches, and avoid
  Airtest's Python/OpenCV/NumPy integration problems.
- Report success, or the last valid result and the failed operation.
- Ship visible, usable template images with image-based examples.

Sources: [framework requirements](android-requirements.md),
[usage guide](android-usage.md), [API documentation](swiftest.md), and user messages in
threads `01a1a086-553e-7bd2-99eb-7b9e7f2ccf2c`,
`01a1b3d7-5988-7462-a21e-efb23d579028`, and
`01a1b5dd-4ae0-7752-a6fa-34dfc80f10ec`; current review conversation.
Conversation exports are not distributed in Git. Documentation that conflicts
with a later user correction must be updated; existing implementation is evidence
of current behavior, not authority to redefine the requirement.

## What Airtest actually supplies

Airtest image tests are ordinary Python. Its IDE records crops, stores image
metadata and displays images in the editor. This is a useful authoring baseline:
actions and their visual targets are directly reviewable.
[Official image-script guide](https://airtest.doc.io.netease.com/en/IDEdocs/airtest_framework/3_airtest_image/).

`touch(Template(...))` already searches until a target is found or the lookup
times out. `exists()` also performs a timed search and returns a usable position;
following it with another template touch repeats the lookup. Airtest also offers
launch, swipe, key/text input, assertions, command-line execution and reports.
It is inaccurate to say that it has no automatic waiting.
[Action API](https://raw.githubusercontent.com/AirtestProject/Airtest/master/airtest/core/api.py),
[framework documentation](https://airtest.doc.io.netease.com/en/).

Its templates contain recorded position/resolution, click-anchor and scale
metadata. Matching can try multiple algorithms. The standard lookup path
captures, matches, invokes an optional failure callback and sleeps before retrying;
the default interval is 0.5 seconds. That callback is not a UI-change event.
The opportunity is coordinated recognition, execution and outcome checking, not
merely adding a wait around a click.
[Matching implementation](https://raw.githubusercontent.com/AirtestProject/Airtest/master/airtest/core/cv.py).

Current upstream requirements constrain NumPy below 2 and OpenCV contrib to
4.6.0.66 or earlier. SwifTest should validate a useful dependency compatibility
range; permissive package metadata alone does not establish compatibility.
[Airtest requirements](https://raw.githubusercontent.com/AirtestProject/Airtest/master/requirements.txt).

These are inspected/documented properties, not new local speed measurements.
The existing [lifecycle analysis](airtest-lifecycle-analysis-2026-11-07.md)
has further deployment and runtime evidence. Its historical implementation
status must be read with the current audit below.

## Current implementation and drift

| Area | Evidence at `43a46d1` | Assessment |
| --- | --- | --- |
| Simple scripts | `examples/genshin/test_teleport.py` has a prompt dictionary, `while`, `wait_any`, state branches, prompt removal and explicit waits | Image filename shorthand improved syntax but did not meet the authoring boundary |
| Launch | `Session.open` dispatches package launch only | Gameplay readiness and entry operations remain outside that call; avoid claiming otherwise |
| Geometry | `targets.py` supports region, expected position/tolerance, size, scale, mask, normalized positions and parent/child `Dialog`; touch supports offsets | Substantial existing support; general relations such as left-of or above an independent control are not implemented |
| Content and variants | Text, image alternatives, variants and registered pop-ups exist | Useful components; handling still relies on supplied UI facts/policies, not arbitrary unseen-dialog understanding |
| Action execution | `Session.touch` owns lookup, guarded dispatch and an optional expected result; repeated dispatch requires explicit safety/result information | Preserve this base; ordinary flow composition still leaves orchestration in the test |
| Observations | Shared lazy observations, exact-region result reuse and streaming frame notifications exist | Frame notifications are not semantic game events; changing pixels still require evaluation |
| Images and authoring | Six real PNG crops and a gallery are supplied | Assets now exist; there is no AirtestIDE-equivalent recorder or inline-image editor |
| Migration and distribution | `compat.py`, `convert.py`, standalone package builder and tests exist | Compatibility is a documented subset, not full Airtest equivalence |
| Outcomes | Tracked operations, explicit postconditions and last-result/failed-intent reporting exist | Input dispatch is not proof that the game reached the intended state |
| Speed and energy | Dated local experiments document gains, failures and an unresolved long arrival delay | No general human-speed or energy-saving claim is established |

Two documentation errors also need correction. Requiring a catalog or assigning
procedural recovery to the test project contradicts the ordinary authoring goal.
Treating cold-start elapsed time as the product's primary responsiveness measure
contradicts the later user correction. Historical cold benchmarks remain useful,
but must not replace measurement of automation-added delay.

## Decisions and the next acceptance check

Retain Python actions and inspectable image/text/geometry information. Do not add
a natural-language layer, require a per-game setup, replace pixel recognition
with Poco, or hide a game state machine in a helper. Preserve existing geometry,
ambiguity, freshness and outcome checks while moving execution mechanics into
the reusable runtime. This review does not select or promise an unimplemented API.

Before accepting the next implementation, compare equivalent ordinary Airtest
and SwifTest scripts, counting all required helper/profile/setup code. Instrumented
benchmark scripts are not representative authoring examples. The SwifTest case
must express game operations without manual sleep, polling or retry loops.

Use the same declared operations on a cold entry screen, an already-ready game,
and a delayed-loading/known-interruption path. Check exact action order and the
observed outcome. Include a duplicate-looking control outside the expected area
and a moved dialog with a relative child: relaxing image similarity must not
silently relax geometry or authorize a wrong target.

Measure from independently identified actionable UI to input, and from achieved
result to reported completion. Separate acquisition, recognition and dispatch
costs from game loading and setup. Compare matched trials with Airtest and a
human timing reference; report failures, transfer/work counts and temperature
alongside latency. Reject an apparent simplification that merely moves game
orchestration elsewhere, or a speed gain that adds wrong/duplicate input.

Review-phase verification: repository docs and user messages checked; current
runtime/examples and primary Airtest sources inspected. No new device run,
performance cohort or runtime modification was made for this review.

## Implementation follow-up: 0.5.0

**Type and impact:** additive behavior/API and authoring changes. The ordinary
Genshin script now has four operation calls and one ready-screen definition. Its
startup loop, prompt bookkeeping, explicit waits and redundant final assertion
are gone. `open_app(..., through=[...], expect=...)` owns progression over declared
entry controls and verifies readiness. The runner supplies execution deadlines.
No app-specific profile, helper or natural-language layer is involved.

`Relative(target, below=anchor, ...)` adds above/below/left/right/near relations
between independent controls. Image filenames compose directly inside relative,
dialog, alternative, variant and absence selectors. Python and standard JSON
share the implementation. The main usage guide now uses portable Python commands
instead of PowerShell setup and report-processing instructions.

**Scope and risk:** existing plain launch remains dispatch-only. Entry targets
are optional progression steps; mandatory actions remain ordinary touches. The
runtime shares observations and input guards, never repeats an entry tap, rejects
ambiguous choices, and propagates transport failures. Target geometry and existing
retry safeguards remain enforced. This does not add unknown-dialog understanding,
an IDE/recorder, or a measured general speed/energy advantage.

**Verification:** 141 offline tests pass, including delayed entry, already-ready,
mid-entry, known interruption, ambiguous controls/readiness, missing outcomes,
lost acknowledgement, moved anchors/dialogs, wrong-side distractors and JSON.
Two live Genshin runs pass: five inputs from the entry screens and three when
already running, with no OCR or hierarchy reads. A final arrival screenshot was
visually checked. These PNG-capture runs are functional checks, not performance
comparisons. The phone's previous Settings foreground was restored.

The baseline gap table above remains a record of `43a46d1`. Startup orchestration,
independent-control relations and composite filename authoring are closed by this
follow-up. Broad device/layout coverage, visual recording and independently
measured human-speed/energy targets remain open and are not implied by test counts.
