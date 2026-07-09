import numpy as np

class DriverCVSimulator:
    def generate_frame(self):
        """Generates a dummy frame and telemetry for simulation."""
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        telemetry = {"speed": 65.0}
        return frame, telemetry

driver_cv_simulator = DriverCVSimulator()
