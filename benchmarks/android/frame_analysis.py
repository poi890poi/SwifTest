"""Offline classifiers for the historical screenshot benchmarks."""

import re

ENTRY_LABELS = (
    "輕按螢幕進入",
    "轻触屏幕进入",
    "點擊進入",
    "点击进入",
    "點擊開始",
    "点击开始",
    "startgame",
    "taptobegin",
    "taptoenter",
)


def compact(text):
    return (
        re.sub(r"\s+", "", text)
        .casefold()
        .translate(str.maketrans("傳送錨點", "传送锚点"))
    )


def matching_line(observation, labels, region=None, exact=False):
    """Match a complete OCR line and return its observed bounds, never guessed text."""
    width, height = observation["width"], observation["height"]
    for line in observation.get("lines", []):
        value = compact(line["text"])
        if not any(
            value == compact(label) if exact else compact(label) in value
            for label in labels
        ):
            continue
        words = line.get("words", [])
        if not words:
            continue
        left, top = min(w["x"] for w in words), min(w["y"] for w in words)
        right = max(w["x"] + w["width"] for w in words)
        bottom = max(w["y"] + w["height"] for w in words)
        x, y = (left + right) / 2, (top + bottom) / 2
        if region and not (
            region[0] <= x / width <= region[2] and region[1] <= y / height <= region[3]
        ):
            continue
        return {"text": line["text"], "x": x, "y": y}
    return None


def classify(observation, world_hud=False):
    text = compact(" ".join(line["text"] for line in observation.get("lines", [])))
    if any(
        s in text
        for s in ("4201", "網路錯誤", "网络错误", "networkerror", "無法連接網路")
    ):
        return "network_error"
    if any(
        s in text for s in ("輸入密碼", "输入密码", "enterpassword", "驗證碼", "验证码")
    ):
        return "login_required"
    if any(
        s in text
        for s in ("下載", "下载", "downloading", "檢查更新", "检查更新", "verifying")
    ):
        return "downloading"
    shader_label = "色器" in text and ("編" in text or "编" in text)
    if shader_label or any(
        s in text for s in ("著色器", "着色器", "compilingshaders", "解壓縮", "解压缩")
    ):
        return "preparing"
    if entry_button(observation):
        return "start"
    teleport = matching_line(
        observation, ("傳送", "传送", "teleport"), region=(0.65, 0.65, 1, 1), exact=True
    )
    waypoint = matching_line(
        observation,
        (
            "傳送錨點",
            "传送锚点",
            "传送點",
            "傳送點",
            "传送点",
            "teleportwaypoint",
            "七天神像",
            "statueofthe",
        ),
        region=(0.6, 0, 1, 0.40),
    )
    if teleport and waypoint:
        return "waypoint_selected"
    if world_hud:
        return "world"
    if matching_line(
        observation,
        ("提瓦特", "teyvat", "探索度", "explorationprogress"),
        region=(0.65, 0.65, 1, 1),
    ):
        return "map"
    return "unknown"


def entry_button(observation):
    button = matching_line(observation, ENTRY_LABELS, region=(0.15, 0.45, 0.85, 1))
    if button:
        # Logical identity, not raw OCR spelling, owns retry timing.
        launch = any(compact(label) in compact(button["text"])
                     for label in ("點擊開始", "点击开始", "startgame"))
        return dict(button, stage="launch" if launch else "enter")
    # Current Chinese launch UI uses 開始遊戲. OCR can misread its final two
    # characters against the animated background; require the server selector
    # as independent context before accepting the stable 開始 prefix.
    server = matching_line(observation, ("Asia", "Europe", "America", "TW, HK, MO"),
                           region=(0.30, 0.70, 0.70, 0.91), exact=True)
    if server:
        button = matching_line(observation, ("開始", "开始"),
                               region=(0.40, 0.40, 0.60, 0.58))
        return dict(button, stage="launch") if button else None
    version = matching_line(observation, ("OSREL",), region=(0, 0.94, 0.5, 1))
    if version:
        # RapidOCR can omit 螢 in the small footer prompt. Keep this observed
        # alias exact and require the game's release footer as context.
        button = matching_line(observation, ("輕按幕進入", "轻按幕进入"),
                               region=(0.35, 0.85, 0.65, 0.98), exact=True)
        return dict(button, stage="enter") if button else None
    return None


def has_world_hud(image, observation):
    """Require both UID text and the distinctive bottom-center green HP bar."""
    import cv2
    import numpy as np

    if not matching_line(observation, ("uid",), region=(0.70, 0.85, 1, 1)):
        return False
    # Portable OCR can also read the numerical health label on a partially filled bar.
    has_level = matching_line(observation, ("lv.",), region=(0.3, 0.82, 0.60, 0.98))
    for line in observation.get("lines", []):
        health = re.fullmatch(r"(\d+)\s*/\s*(\d+)", line["text"])
        if (
            has_level
            and health
            and 0 < int(health[1]) <= int(health[2])
            and matching_line(
                observation,
                (line["text"],),
                region=(0.37, 0.82, 0.65, 0.98),
                exact=True,
            )
        ):
            return True
    h, w = image.shape[:2]
    crop = image[int(h * 0.82) : int(h * 0.97), int(w * 0.32) : int(w * 0.68)]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array([35, 70, 80]), np.array([85, 255, 255]))
    contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    if any(
        bw > w * 0.07 and bw > bh * 12 and bh >= 2
        for _, _, bw, bh in (cv2.boundingRect(c) for c in contours)
    ):
        return True
    # On the phone the health readout divides the bright bar into two halves.
    bright = cv2.inRange(hsv, np.array([28, 50, 180]), np.array([85, 255, 255]))
    contours = cv2.findContours(bright, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[-2]
    segments = sorted(cv2.boundingRect(c) for c in contours)
    segments = [
        (x, y, bw, bh)
        for x, y, bw, bh in segments
        if 0.04 * w < bw < 0.10 * w and bw > 7 * bh and bh >= 2
    ]
    center = crop.shape[1] / 2
    for left, right in zip(segments, segments[1:]):
        x, y, bw, bh = left
        rx, ry, rw, rh = right
        if (
            x < center < rx + rw
            and abs(y - ry) <= h * 0.006
            and 0 < rx - x - bw < w * 0.045
            and abs(bw - rw) < w * 0.025
            and abs(bh - rh) <= h * 0.007
        ):
            return True
    return False


def is_loading_screen(image):
    """Conservative visual loading cue; an OCR miss alone is not a transition."""
    import cv2
    import numpy as np

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    neutral = hsv[:, :, 1] < 35
    bright = neutral & (hsv[:, :, 2] > 220)
    dark = hsv[:, :, 2] < 35
    return float(np.mean(bright)) > 0.80 or float(np.mean(dark)) > 0.90


def brightness_percentile(image):
    """Exact 99.5th percentile for 8-bit frames, without partitioning the pixels."""
    import cv2
    import numpy as np

    # Float histograms count integers exactly only up to 2**24. Retain the
    # original operation for other image types and unusually large frames.
    if image.dtype != np.uint8 or not 0 < image.size <= 2**24:
        return float(np.percentile(image, 99.5))
    counts = cv2.calcHist([image.reshape(-1, 1)], [0], None, [256], [0, 256]).ravel()
    cumulative = counts.cumsum(dtype=np.float64)
    rank = .995 * (image.size - 1)
    low, high = np.searchsorted(cumulative, [int(rank), int(np.ceil(rank))], side="right")
    fraction = rank - int(rank)
    return float(high - (high - low) * (1 - fraction) if fraction >= .5
                 else low + (high - low) * fraction)


def ocr_image(image):
    """Recover OCR contrast when Samsung's idle overlay dims the captured game."""
    import cv2

    level = brightness_percentile(image)
    if 3 < level < 65:
        return cv2.convertScaleAbs(image, alpha=min(16.0, 230.0 / level))
    return image
