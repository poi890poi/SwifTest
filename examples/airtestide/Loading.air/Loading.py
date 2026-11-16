"""Run the loading-screen example on the SwifTest Android fixture."""

from swiftest import open_app, screen_signature, touch, wait, wait_screen_change
from swiftest.compat import Template

open_app("org.swiftest.variantsfixture", activity=".LoadingActivity")
start = Template(r"start.png", threshold=0.85)
wait(start)
before = screen_signature(samples=3)
touch(start)
wait_screen_change(before, timeout=15)
