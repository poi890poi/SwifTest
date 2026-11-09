"""Template-based example; see README.md for the recorded layout and prerequisites."""

from swiftest import Position, Template, open_app, touch


def test_teleport():
    ready = Template("assets/level.png", threshold=.8, region=(.36, .87, .45, .97))
    open_app("com.miHoYo.GenshinImpact",
             through=[Template("assets/entry.png", threshold=.75), "assets/door.png"],
             expect=ready)
    touch(Position(.085, .145), expect="assets/map.png")
    touch(Position(.499, .498), expect="assets/waypoint_title.png")
    touch("assets/teleport.png", expect=ready)
