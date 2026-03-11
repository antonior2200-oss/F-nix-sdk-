import numpy as np

class CommandBus:
    def __init__(self, max_agents: int):
        self._cmd = np.zeros((max_agents, 3), dtype=np.float32)
        self._dirty = np.zeros((max_agents,), dtype=np.bool_)

    def set_cmd(self, aid: int, vx: float, vy: float, vz: float):
        self._cmd[aid, 0] = vx
        self._cmd[aid, 1] = vy
        self._cmd[aid, 2] = vz
        self._dirty[aid] = True

    def snapshot(self):
        cmd = self._cmd.copy()
        dirty = self._dirty.copy()
        self._dirty[:] = False
        return cmd, dirty
