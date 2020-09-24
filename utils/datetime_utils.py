# pylint: disable=old-division


def get_diff_milliseconds(end: int, start: int) -> int:
    """Get the milliseconds between two timestamps (seconds)."""
    if start > end:
        start, end = end, start
    elapsed = end - start
    return elapsed.seconds * 1000 + elapsed.microseconds / 1000
