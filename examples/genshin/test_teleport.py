"""Template-based example; see README.md for the recorded layout and prerequisites."""

from swiftest import Position, Template, open_app, touch, wait, wait_any, assert_exists


def test_teleport():
    open_app("com.miHoYo.GenshinImpact")
    ready = Template("assets/level.png", threshold=.8, region=(.36, .87, .45, .97))
    prompts = {"start": Template("assets/entry.png", threshold=.75), "enter": "assets/door.png"}
    while prompts:
        state = wait_any({"ready": ready, **prompts}, timeout=240)["condition"]
        if state == "ready":
            break
        touch(prompts.pop(state))
    wait(ready, timeout=240)

    touch(Position(.085, .145), expect="assets/map.png")
    touch(Position(.499, .498), expect="assets/waypoint_title.png")
    touch("assets/teleport.png", expect=ready, timeout=90)
    assert_exists(ready)
