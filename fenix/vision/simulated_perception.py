
import math
from typing import List, Tuple

import numpy as np


class VirtualObject:
    def __init__(self, cls: str, position: np.ndarray,
                 velocity: np.ndarray = None, priority: float = 1.0):
        self.cls = cls
        self.position = position.astype(np.float32)
        self.velocity = velocity.astype(np.float32) if velocity is not None else np.zeros(3, dtype=np.float32)
        self.priority = priority


class SimulatedPerceptionEngine:
    def __init__(self, hvu_pos: Tuple[float, float, float], config):
        self.hvu = np.array(hvu_pos, dtype=np.float32)
        self.objects: List[VirtualObject] = []
        self.config = config
        self._init_objects()

    def _init_objects(self):
        classes = ["vehicle", "person", "structure", "unknown"]
        angles = np.linspace(0, 2 * math.pi, self.config.SIM_OBJECT_COUNT, endpoint=False)
        for i, a in enumerate(angles):
            pos = self.hvu + np.array([80 * math.cos(a), 80 * math.sin(a), 0], dtype=np.float32)
            vel = np.random.normal(0, 2, 3).astype(np.float32)
            priority = np.random.uniform(0.5, 1.0)
            self.objects.append(VirtualObject(classes[i % len(classes)], pos, vel, priority))

    def generate(self, states: np.ndarray):
        if len(states) == 0:
            return []
        # aquí portas tu lógica de SimulatedDetection
        return []
