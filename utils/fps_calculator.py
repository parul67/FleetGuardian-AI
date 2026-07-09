import time
from collections import deque

class FPSCalculator:
    """
    Tracks video stream processing speed using a sliding window of recent timestamps.
    """
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.timestamps = deque(maxlen=window_size)
        self.prev_time = 0.0

    def start(self):
        """Resets the timer starting point."""
        self.prev_time = time.perf_counter()
        self.timestamps.clear()

    def update(self) -> float:
        """
        Record a frame completion and return the rolling average FPS.
        """
        curr_time = time.perf_counter()
        self.timestamps.append(curr_time)
        self.prev_time = curr_time

        if len(self.timestamps) < 2:
            return 0.0

        # Calculate time elapsed between first and last timestamp in the sliding window
        total_time = self.timestamps[-1] - self.timestamps[0]
        if total_time <= 0.0:
            return 0.0

        # FPS is (number of intervals) / total_time
        return (len(self.timestamps) - 1) / total_time

    @property
    def fps(self) -> float:
        """Returns current average FPS without appending a new frame timestamp."""
        if len(self.timestamps) < 2:
            return 0.0
        total_time = self.timestamps[-1] - self.timestamps[0]
        if total_time <= 0.0:
            return 0.0
        return (len(self.timestamps) - 1) / total_time
