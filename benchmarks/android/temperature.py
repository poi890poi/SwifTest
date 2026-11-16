"""Summarize Android battery and thermal sensor samples."""

import re


def parse_temperatures(battery, thermal):
    result = {}
    for line in battery.splitlines():
        match = re.match(r"\s*(temperature|level|status|USB powered):\s*(.+)", line)
        if match:
            key, value = match.groups()
            if key == "temperature":
                result["battery_c"] = int(value) / 10
            else:
                result[key] = value
    # Prefer the fresh HAL section over cached listener temperatures.
    current = thermal.split("Current temperatures from HAL:")[-1]
    for value, kind, name, status in re.findall(
            r"Temperature\{mValue=([\d.-]+), mType=(\d+), mName=([^,]+), mStatus=(\d+)\}", current):
        if name in ("AP", "SKIN", "BAT"):
            result[name + "_c"] = float(value)
            result[name + "_status"] = int(status)
    match = re.search(r"Thermal Status:\s*(\d+)", thermal)
    if match:
        result["thermal_status"] = int(match[1])
    return result


def temperature_summary(samples):
    summary = {}
    for name in ("battery_c", "AP_c", "SKIN_c"):
        values = [s[name] for s in samples if name in s]
        if values:
            summary[name] = dict(start=values[0], end=values[-1], peak=max(values),
                                 delta=round(values[-1]-values[0], 3))
    return summary
