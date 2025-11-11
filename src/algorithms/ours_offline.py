from src.algorithms.base import BaseOfflineSolver
from src.schedule import Schedule
from src.algorithms.our.get_lower_bound_by_greedy import lower_bound
from src.algorithms.our.get_upper_bound_by_LP import get_upper_bound_by_LP

from tqdm import tqdm
import time

from typing import Dict, Optional, Any, List, Tuple


class OurOffline(BaseOfflineSolver):
    def __init__(self):
        super().__init__()

    def schedule(self, schedule: Schedule) -> Schedule:
        best_upper_case = float('-inf')
        best_lower_case = float('-inf')
        best_lower_case_correct = float('-inf')
        best_schedule = None
        pruned = 0

        # add all of the possible candidates at t=1
        # assert schedule.t == -1, f"Provided schedule must be at t=-1, but got t={schedule.t}"
        candidates = schedule.get_candidates()

        # print('Got candidates: ', len(candidates))

        # while candates are not empty, expend
        

        # start_time = time.time()
        

        # Initialize tqdm progress bar (updates only bar, does not change inner logic)
        with tqdm(total=0, position=0, leave=True, desc="Candidates in queue", dynamic_ncols=True) as pbar:
            while len(candidates) != 0:
                # * 1. check that every candidate has a lower and upper bound
                prune_list = []
                for i in range(len(candidates)): # O(n)  - should be okay
                    if candidates[i].lower_bound is None:
                        candidates[i].lower_bound = lower_bound(candidates[i])
                    if candidates[i].upper_bound is None:
                        candidates[i].upper_bound = get_upper_bound_by_LP(candidates[i])

                    # * 2. If a candidate has a lower UPPER bound than the best LOWER bound, we prune it
                    if candidates[i].upper_bound <= best_lower_case:
                        prune_list.append(i)
                        pruned += 1

                prune_list.sort(reverse=True)
                candidates = [c for j, c in enumerate(candidates) if j not in prune_list]
                # for j, i in enumerate(prune_list):
                    # del candidates[i - j]

                # We somehow pruned everything...
                if len(candidates) == 0:
                    break

                # # * 3. Select candidate with highest upper bound
                # best_candidate = max(candidates, key=lambda x: x.upper_bound)
                # candidates.remove(best_candidate)

                # * 3. Select candidate with highest upper bound, then by highest lower bound
                best_candidate = max(
                    candidates,
                    key=lambda x: (x.lower_bound, x.upper_bound)  # first order by the highest lower bound, then break ties by the highest upper bound
                )
                candidates.remove(best_candidate)
                
                # * 3. Select candidate with highest lower bound
                # best_candidate = max(candidates, key=lambda x: x.lower_bound)
                # candidates.remove(best_candidate)

                # * 4. Check if it's a complete schedule, otherwise expand it
                # When t == T-1, we've scheduled all T time slots (complete schedule)
                candidate_score = best_candidate.score_rewritten()
                if candidate_score > best_lower_case:
                    best_lower_case = candidate_score
                    best_schedule = best_candidate
                    best_lower_case_correct = best_candidate.score()
                
                if best_candidate.t < best_candidate.T - 1:
                    # Complete schedule - evaluate it
                    # candidate_score = best_candidate.score()
                # else:
                    # Expand the candidate
                    new_candidates = best_candidate.get_candidates()
                    candidates.extend(new_candidates)

                # Update tqdm bar (without altering code behavior)
                # elapsed = time.time() - start_time
                pbar.set_description(f"Candidates: {len(candidates)} | Best Lower: {best_lower_case:0.2f} (true: {best_lower_case_correct:0.2f}) | Best Upper: {best_candidate.upper_bound:0.2f} | Pruned branches: {pruned}")
                pbar.n = len(candidates)
                pbar.refresh()

                if all(candidate.upper_bound <= best_lower_case for candidate in candidates):
                    break  # we found AN optimal schedule

        return best_schedule
        
        