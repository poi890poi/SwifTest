"""Replay historical classifier cases on synthetic observations."""
import unittest

from benchmarks.android.frame_analysis import classify, matching_line, has_world_hud, is_loading_screen, ocr_image


def observation(*entries):
    return {
        "width": 2400,
        "height": 1080,
        "lines": [
            {
                "text": text,
                "words": [{"text": text, "x": x, "y": y, "width": 100, "height": 30}],
            }
            for text, x, y in entries
        ],
    }


class FrameAnalysisTests(unittest.TestCase):
    def test_network_error_overrides_other_screen_evidence(self):
        obs = observation(("網 路 錯 誤", 900, 200), ("錯誤碼：4201", 900, 500))
        self.assertEqual(classify(obs, world_hud=True), "network_error")

    def test_chinese_ocr_character_spacing_and_bounds(self):
        obs = observation(("傳 送", 2100, 990))
        result = matching_line(obs, ("傳送",), (0.65, 0.65, 1, 1), exact=True)
        self.assertEqual((result["x"], result["y"]), (2150, 1005))

    def test_teleport_word_in_description_is_not_a_button(self):
        obs = observation(
            ("傳送錨點", 1900, 200), ("使用傳送錨點前往目的地", 1900, 800)
        )
        self.assertNotEqual(classify(obs), "waypoint_selected")

    def test_teleport_requires_waypoint_context_and_button_region(self):
        for obs in (
            observation(("傳送", 2100, 990)),
            observation(("傳送錨點", 1900, 200), ("傳送", 200, 500)),
        ):
            self.assertNotEqual(classify(obs), "waypoint_selected")
        good = observation(("傳送錨點", 1900, 200), ("傳送", 2100, 990))
        self.assertEqual(classify(good), "waypoint_selected")

    def test_download_does_not_count_as_ready(self):
        self.assertEqual(
            classify(observation(("正在下載資源 42%", 900, 800))), "downloading"
        )

    def test_start_requires_observed_text_in_lower_screen(self):
        self.assertEqual(classify(observation(("點 擊 進 入", 1100, 900))), "start")
        self.assertEqual(
            classify(observation(("輕 按 螢 幕 進 入", 1100, 990))), "start"
        )
        self.assertEqual(classify(observation(("點 擊 進 入", 1100, 100))), "unknown")

    def test_current_start_screen_requires_server_context(self):
        for text in ("開始遊戲", "開始游獻", "开始游戏"):
            self.assertEqual(classify(observation((text, 1100, 490),
                                                  ("Asia", 1150, 880))), "start")
            self.assertEqual(classify(observation((text, 1100, 490))), "unknown")
            self.assertEqual(classify(observation((text, 100, 490),
                                                  ("Asia", 1150, 880))), "unknown")

    def test_ocr_omitted_entry_glyph_requires_release_footer(self):
        prompt = ("輕按幕進入", 1120, 990)
        self.assertEqual(classify(observation(prompt, ("OSRELAndroid7.2.0", 180, 1038))), "start")
        self.assertEqual(classify(observation(prompt)), "unknown")
        self.assertEqual(classify(observation(("輕按幕進入", 1120, 400),
                                              ("OSRELAndroid7.2.0", 180, 1038))), "unknown")

    def test_region_map_uses_exploration_label_in_footer(self):
        self.assertEqual(classify(observation(("探 索 度 1%", 2000, 1030))), "map")
        self.assertEqual(classify(observation(("探 索 度 1%", 400, 300))), "unknown")

    def test_split_hp_bar_on_green_terrain(self):
        import numpy as np

        frame = np.full((1080, 2400, 3), (61, 115, 42), dtype=np.uint8)
        obs = observation(("UID: 123456789", 2150, 960))
        for left in (1010, 1234):
            frame[985:999, left : left + 155] = (50, 210, 80)
        self.assertTrue(has_world_hud(frame, obs))
        frame[985:999, 1234:1389] = (61, 115, 42)
        self.assertFalse(has_world_hud(frame, obs))

    def test_uid_alone_on_loading_screen_is_not_world(self):
        import numpy as np

        frame = np.full((1080, 2400, 3), 245, dtype=np.uint8)
        obs = observation(("UID: 123456789", 2150, 1040))
        self.assertFalse(has_world_hud(frame, obs))
        self.assertTrue(is_loading_screen(frame))
        frame[960:966, 1000:1400] = (50, 210, 80)
        self.assertTrue(has_world_hud(frame, obs))

    def test_dimmed_ocr_preprocessing_preserves_original(self):
        import numpy as np

        frame = np.full((100, 100, 3), 20, dtype=np.uint8)
        corrected = ocr_image(frame)
        self.assertGreater(float(corrected.mean()), 150)
        self.assertEqual(int(frame.max()), 20)
        self.assertEqual(corrected.shape, frame.shape)
