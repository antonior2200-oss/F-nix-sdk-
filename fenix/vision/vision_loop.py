import asyncio
import logging
import time
from typing import Optional, List

import numpy as np

class VisionLoop:
    def __init__(self, perception_engine=None, vision_client=None,
                 recorder=None, reactor=None, config=None):
        self.perception_engine = perception_engine
        self.vision_client = vision_client
        self.recorder = recorder
        self.reactor = reactor
        self.config = config
        self.alert = False
        self.last_detections: List = []
        self.last_detection_time: float = 0.0
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(1)
        self.logger = logging.getLogger("VisionLoop")

    async def start(self):
        self.running = True
        self._task = asyncio.create_task(self._loop())
        self.logger.info("VisionLoop iniciado")

    async def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def feed_states(self, states: np.ndarray):
        if self.perception_engine is None or not self.running:
            return
        if self._semaphore.locked():
            return
        asyncio.create_task(self._sim_perception_step(states))

    async def _sim_perception_step(self, states: np.ndarray):
        async with self._semaphore:
            await asyncio.sleep(self.config.SIM_DET_LATENCY)
            dets = self.perception_engine.generate(states)
            self._handle_detections(dets, sim=True)

    async def _loop(self):
        interval = 1.0 / self.config.VISION_POLL_HZ
        while self.running:
            try:
                await asyncio.sleep(interval)
                if self.vision_client is None:
                    continue
                frame = await self._capture_frame()
                if frame is None:
                    continue
                dets = await self.vision_client.detect_image_bytes(frame)
                self._handle_detections(dets, sim=False)
            except asyncio.CancelledError:
                break
            except Exception as exc:
                self.logger.error(f"VisionLoop error: {exc}", exc_info=True)
                await asyncio.sleep(1.0)

    def _handle_detections(self, dets, sim: bool):
        self.last_detections = dets
        self.last_detection_time = time.time()
        self.alert = any(getattr(d, "conf", 1.0) >= self.config.VISION_MIN_CONF for d in dets)
        if self.reactor:
            self.reactor.update(dets)
        if sim and dets and self.recorder:
            # aquí puedes portar tu lógica de logging simulado
            pass

    async def _capture_frame(self) -> Optional[bytes]:
        # Implementación específica del usuario
        return None
