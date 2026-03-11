import logging
import time
from typing import List, Dict, Tuple

import numpy as np

class PerceptionReactor:
    def __init__(self, predictive_planner, config):
        self.predictive_planner = predictive_planner
        self.dynamic_targets: List[Dict] = []
        self.config = config
        self.logger = logging.getLogger("PerceptionReactor")

    def update(self, detections: List):
        now = time.time()
        for det in detections:
            if getattr(det, "conf", 1.0) < self.config.VISION_MIN_CONF:
                continue
            obj_id = self.predictive_planner.register_detection(det)
            target = {
                "pos": np.array([det.x, det.y, det.z]),
                "priority": getattr(det, "priority", 1.0),
                "obj_id": obj_id,
                "expiry": now + self.config.TARGET_LIFETIME,
            }
            found = False
            for i, t in enumerate(self.dynamic_targets):
                if t["obj_id"] == obj_id:
                    self.dynamic_targets[i] = target
                    found = True
                    break
            if not found:
                self.dynamic_targets.append(target)

        self.dynamic_targets = [t for t in self.dynamic_targets if t["expiry"] > now]
        if len(self.dynamic_targets) > self.config.MAX_DYNAMIC_TARGETS:
            self.dynamic_targets.sort(key=lambda x: -x["priority"])
            self.dynamic_targets = self.dynamic_targets[:self.config.MAX_DYNAMIC_TARGETS]

    def get_targets(self) -> Tuple[np.ndarray, np.ndarray]:
        if not self.dynamic_targets:
            return np.empty((0, 3)), np.empty(0)
        pos = np.array([t["pos"] for t in self.dynamic_targets])
        pri = np.array([t["priority"] for t in self.dynamic_targets])
        return pos, pri
