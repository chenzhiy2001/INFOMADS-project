from src.algorithms.base import BaseOfflineSolver
from src.schedule import Schedule

from typing import Dict, Optional, Any, List, Tuple
import copy


# Placeholder bounds. Implementations should be provided elsewhere or replaced here.
# New signature: bounds depend on the current partial Schedule and the next time step to expand.
def get_lower_bound(partial_schedule: Schedule, next_time_step: int) -> float:
    raise NotImplementedError("get_lower_bound() is a placeholder; provide an implementation.")


def get_upper_bound(partial_schedule: Schedule, next_time_step: int) -> float:
    raise NotImplementedError("get_upper_bound() is a placeholder; provide an implementation.")


class OurOffline(BaseOfflineSolver):
    def __init__(self):
        super().__init__()

    @staticmethod
    def get_lower_bound(partial_schedule: Schedule, next_time_step: int) -> float:
        pass

    def schedule(self, schedule: Schedule) -> Schedule:
        
        candidates = []

        