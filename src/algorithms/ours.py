from src.algorithms.base import BaseOfflineSolver
from src.schedule import Schedule
from src.algorithms.our.get_lower_bound_by_greedy import lower_bound
from src.algorithms.our.get_upper_bound_by_LP import get_upper_bound_by_LP

from typing import Dict, Optional, Any, List, Tuple


class OurOffline(BaseOfflineSolver):
    def __init__(self):
        super().__init__()

    def schedule(self, schedule: Schedule) -> Schedule:
        best_upper_case = float('-inf')
        best_lower_case = float('-inf')
        best_schedule = None

        # add all of the possible candidates at t=1
        assert schedule.t == -1, f"Provided schedule must be at t=-1, but got t={schedule.t}"
        candidates = schedule.get_candidates()

        # print('Got candidates: ', len(candidates))

        # while candates are not empty, expend
        while len(candidates) != 0:
            print('candidates: ', len(candidates))

            # * 1. check that every candidate has a lower and upper bound
            prune_list = []
            for i in range(len(candidates)): # O(n)  - should be okay
                if candidates[i].lower_bound is None:
                    candidates[i].lower_bound = lower_bound(candidates[i])
                if candidates[i].upper_bound is None:
                    candidates[i].upper_bound = get_upper_bound_by_LP(candidates[i])

                # * 2. If a candidate has a lower UPPER bound than the best LOWER bound, we prune it
                if candidates[i].upper_bound < best_lower_case:
                    prune_list.append(i)

            prune_list.sort(reverse=True)
            for j, i in enumerate(prune_list):
                del candidates[i - j]

            # We somehow pruned everything...
            if len(candidates) == 0:
                break

            # * 3. Select candidate with highest upper bound
            best_candidate = max(candidates, key=lambda x: x.upper_bound)
            candidates.remove(best_candidate)
            
            # * 4. Check if it's a complete schedule, otherwise expand it
            if best_candidate.t >= best_candidate.T:
                # Complete schedule - evaluate it
                candidate_score = best_candidate.score()
                if candidate_score > best_lower_case:
                    best_lower_case = candidate_score
                    best_schedule = best_candidate
            else:
                # Expand the candidate
                new_candidates = best_candidate.get_candidates()
                candidates.extend(new_candidates)

        return best_schedule
        
        