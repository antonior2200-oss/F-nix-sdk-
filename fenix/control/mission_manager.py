"""
mission_manager.py — PHOENIX SDK v2.0
=====================================

Decide la misión global del enjambre (intención) de forma:
  - Estable (cooldown + histéresis).
  - Explicable (razones explícitas).
  - Contextual (amenaza, batería, integridad).
  - Desacoplada (no conoce roles ni behaviors).

Responsabilidades:
  - Mantener misión global actual.
  - Cambiar de misión según contexto y prioridades.
  - Evitar oscilaciones (cooldown).
  - Registrar historial de misiones y razones.

NO hace:
  - Asignar roles.
  - Elegir behaviors.
  - Mover drones.
"""

from __future__ import annotations

import logging
import time
from collections import deque
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


_log = logging.getLogger(__name__)


class Mission(Enum):
    PATROL   = auto()
    DEFEND   = auto()
    INTERCEPT = auto()
    RETURN   = auto()
    EVADE    = auto()
    HOLD     = auto()
    IDLE     = auto()


@dataclass
class MissionContext:
    """Resumen mínimo del estado global para decidir misión."""
    threat_level: float          # 0.0–1.0
    avg_battery: float           # 0.0–1.0
    swarm_integrity: float       # 0.0–1.0 (1.0 = todos OK)
    human_override: Optional[Mission] = None


class MissionManager:
    """
    Gestor táctico de misión global del enjambre.
    """

    def __init__(
        self,
        cooldown_seconds: float = 2.0,
        history_maxlen: int = 50,
    ) -> None:
        self._current: Mission = Mission.IDLE
        self._last_change: float = 0.0
        self._cooldown: float = cooldown_seconds

        self._mission_history: deque[Mission] = deque(maxlen=history_maxlen)
        self._reason_history: deque[str]      = deque(maxlen=history_maxlen)
        self._ctx_history: deque[MissionContext] = deque(maxlen=history_maxlen)

        # Umbrales básicos (ajustables)
        self._threat_defend = 0.4
        self._threat_intercept = 0.7
        self._battery_return = 0.2
        self._integrity_low = 0.6

    # ------------------------------------------------------------
    # API principal
    # ------------------------------------------------------------
    def get_current_mission(self) -> Mission:
        return self._current

    def update_mission(self, ctx: MissionContext) -> Mission:
        """
        Decide si cambiar de misión según el contexto.
        Respeta cooldown y registra historial.
        """
        self._ctx_history.append(ctx)

        # 1. Human override manda siempre (si no viola cooldown crítico)
        if ctx.human_override is not None:
            if self._can_change():
                self._set_mission(ctx.human_override, reason="human_override")
            return self._current

        # 2. Cooldown: si no ha pasado tiempo suficiente, no cambiamos
        if not self._can_change():
            self._reason_history.append("cooldown:hold")
            return self._current

        # 3. Reglas simples pero claras (puedes refinarlas luego)
        new_mission = self._decide_from_context(ctx)

        if new_mission != self._current:
            self._set_mission(new_mission, reason="context_rule")

        return self._current

    # ------------------------------------------------------------
    # Lógica de decisión (puedes hacerla tan rica como quieras)
    # ------------------------------------------------------------
    def _decide_from_context(self, ctx: MissionContext) -> Mission:
        """
        Reglas de ejemplo:
          - Batería muy baja → RETURN.
          - Integridad baja sin amenaza alta → HOLD/REFORM (aquí usamos HOLD).
          - Amenaza muy alta → INTERCEPT.
          - Amenaza media → DEFEND.
          - Sin amenaza → PATROL.
        """
        # Batería crítica
        if ctx.avg_battery < self._battery_return:
            return Mission.RETURN

        # Enjambre roto pero sin amenaza extrema
        if ctx.swarm_integrity < self._integrity_low and ctx.threat_level < self._threat_intercept:
            return Mission.HOLD

        # Amenaza alta
        if ctx.threat_level >= self._threat_intercept:
            return Mission.INTERCEPT

        # Amenaza moderada
        if ctx.threat_level >= self._threat_defend:
            return Mission.DEFEND

        # Sin amenaza relevante
        return Mission.PATROL

    # ------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------
    def _can_change(self) -> bool:
        return (time.monotonic() - self._last_change) >= self._cooldown

    def _set_mission(self, mission: Mission, reason: str) -> None:
        prev = self._current
        self._current = mission
        self._last_change = time.monotonic()
        self._mission_history.append(mission)
        self._reason_history.append(f"{reason}:{prev.name}->{mission.name}")
        _log.debug("Mission change → %s (from %s, reason=%s)", mission, prev, reason)

    # ------------------------------------------------------------
    # Configuración dinámica
    # ------------------------------------------------------------
    def set_cooldown(self, seconds: float) -> None:
        self._cooldown = max(0.0, seconds)
        _log.debug("Mission cooldown → %.2fs", self._cooldown)

    def set_thresholds(
        self,
        *,
        threat_defend: Optional[float] = None,
        threat_intercept: Optional[float] = None,
        battery_return: Optional[float] = None,
        integrity_low: Optional[float] = None,
    ) -> None:
        if threat_defend is not None:
            self._threat_defend = threat_defend
        if threat_intercept is not None:
            self._threat_intercept = threat_intercept
        if battery_return is not None:
            self._battery_return = battery_return
        if integrity_low is not None:
            self._integrity_low = integrity_low
        _log.debug(
            "Mission thresholds → threat_defend=%.2f threat_intercept=%.2f "
            "battery_return=%.2f integrity_low=%.2f",
            self._threat_defend, self._threat_intercept,
            self._battery_return, self._integrity_low,
        )

    # ------------------------------------------------------------
    # Introspección
    # ------------------------------------------------------------
    def debug_state(self) -> dict:
        elapsed = time.monotonic() - self._last_change
        return {
            "current_mission": self._current,
            "cooldown": self._cooldown,
            "cooldown_remaining": max(0.0, self._cooldown - elapsed),
            "mission_history": list(self._mission_history),
            "reason_history": list(self._reason_history),
        }

    def __repr__(self) -> str:
        return (
            f"<MissionManager mission={self._current.name} "
            f"cooldown={self._cooldown}s history={len(self._mission_history)}>"
        )
