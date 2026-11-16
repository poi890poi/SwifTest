"""Open this .air directory in AirtestIDE. Run with swiftest run Level.air."""

from swiftest import wait
from swiftest.compat import Template

# Genshin level label on the original 2400 x 1080 capture.
wait(Template(r"level.png", record_pos=(-0.0945, 0.1883), resolution=(2400, 1080)))
