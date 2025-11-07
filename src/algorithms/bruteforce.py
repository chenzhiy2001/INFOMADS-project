# given jobs, find the optimal scheduling using brute-force search
import copy
from job import Job
from operator import add
from collections.abc import Iterable, Iterator, Sequence
from typing import TypeVar


T = TypeVar("T")


def nth(n: int, it: Iterable[Sequence[T]]) -> Iterator[T]:
    for tup in it:
        yield tup[n]

def two_th(it: Iterable[Sequence[T]]) -> Iterator[T]:
    for tup in it:
        yield tup[1]

# a = [(1, 2), (3, 4)]
# for item in nth(1, a):
#     print(item)
# for item in two_th(a):
#     print(item)

def schedule_counter(job_id, schedule_so_far):
    count = 0
    for schedule_slice in schedule_so_far:
        time_slot = schedule_slice[0]
        scheduled_job_id = schedule_slice[1]
        if scheduled_job_id == job_id:
            count += 1
    return count

class IDCounter:
    def __init__(self):
        self.current_id = 0
    def get_next_id(self):
        id_to_return = self.current_id
        self.current_id += 1
        return id_to_return


def bruteforce_schedule(current_time_slot, job_instances, total_time_slots, reward_so_far, schedule_so_far):
    '''
    psedocode ~~as if we were writing a recursive function~~ We use DFS so the maximum stack depth is total_time_slots, there is no point in implementing fake stack here:
    1. get all available jobs at this time slot, if no available jobs at this time slot and this time slot < total time slots, this time slot ++, append an idle time slot to optimal schedule, repeat
    2. if available jobs exist and this time slot < total time slots,
        1. for each available job
            1. suppose we schedule that job at this time slot,
                1. compute reward incurred by this time slot's assignment
                    1. if this time slot made a job complete, reward_incurred_in_this_time_slot += reward - delay penalty (if any)
                2. make a recursive call to compute the max reward and optimal schedule by [this time slot + 1, total time slots] assignments.
                3. add the reward and optimal schedule from these 2 steps, save it as a candidate solution. add the idle time slot as well
        2. return the maximum reward and corresponding optimal schedule among all candidate solutions.
    3. if no available jobs and this time slot == total time slots,
        1. final_settle = 0
        2. for all jobs:
            1. if job is unfinished, final_settle -= drop penalty + delay penalty (if any)
            2. else if job is not scheduled at all, final_settle -= drop penalty
        4. return final_settle and the corresponding optimal schedule (append an idle time slot to optimal schedule).
    4. if available jobs exist and this time slot == total time slots,
        1. for each available job
            1. suppose we schedule that job at this time slot,
                1. compute reward incurred by this time slot's assignment
                    1. if this time slot made a job complete, reward_incurred_in_this_time_slot += reward - delay penalty (if any)
                2. final_settle = 0
                3. for all jobs:
                    1. if job is unfinished, final_settle -= drop penalty + delay penalty (if any)
                    2. else if job is not scheduled at all, final_settle -= drop penalty
                4. add the reward (by adding reward_incurred_in_this_time_slot and final_settle) and append this job assignment assumption at the optimal schedule, save it as a candidate solution. add the idle time slot as well
        2. return the maximum reward and corresponding optimal schedule among all candidate solutions.
    '''
    # get all available jobs at this time slot
    available_jobs = []
    for job in job_instances:
        if job.release_time <= current_time_slot and schedule_counter(job.id, schedule_so_far) < job.processing_time:
            available_jobs.append(job)
    # if no available jobs at this time slot and this time slot < total time slots, this time slot ++, 
    if not available_jobs and current_time_slot < total_time_slots:
        return bruteforce_schedule(current_time_slot + 1, job_instances, total_time_slots, reward_so_far, schedule_so_far + [(current_time_slot, None)]) # this is a tail recursion where the return value of the last function call is the return value of the first function call
    if available_jobs and current_time_slot < total_time_slots:
        candidate_solutions = []
        for job in available_jobs:
            # suppose we schedule that job at this time slot
            reward_incurred_in_this_time_slot = 0
            # compute reward incurred by this job assignment assumption
            # check if this job is completed at this time slot
            scheduled_time_slots = [time_slot for time_slot, job_id in (schedule_so_far) if job_id == job.id]
            if len(scheduled_time_slots) + 1 == job.processing_time: # job can be completed if we assign it at current_time_slot
                reward_incurred_in_this_time_slot += job.reward
                if current_time_slot > (job.deadline - 1):
                    tardiness = current_time_slot - (job.deadline - 1)
                    reward_incurred_in_this_time_slot -= job.penalty_function.evaluate(tardiness)
            candidate_solutions.append(bruteforce_schedule(
                current_time_slot + 1,
                job_instances,
                total_time_slots,
                reward_so_far + reward_incurred_in_this_time_slot,
                schedule_so_far + [(current_time_slot, job.id)]
            ))
        # consider the idle time slot as well
        candidate_solutions.append(bruteforce_schedule( 
            current_time_slot + 1,
            job_instances,
            total_time_slots,
            reward_so_far,
            schedule_so_far + [(current_time_slot, None)]
        ))
        # return the maximum reward and corresponding optimal schedule among all candidate solutions.
        return max(candidate_solutions, key=lambda x: x[0])
    if not available_jobs and current_time_slot == total_time_slots:
        final_settle = 0
        for job in job_instances:
            if schedule_counter(job.id, schedule_so_far) == 0:
                # job is not scheduled at all
                final_settle -= job.drop_penalty
            elif schedule_counter(job.id, schedule_so_far) < job.processing_time:
                # job is unfinished
                final_settle -= job.drop_penalty
                # check if job is delayed
                last_scheduled_time_slot = max(time_slot for time_slot, job_id in (schedule_so_far) if job_id == job.id)
                if last_scheduled_time_slot > (job.deadline - 1):
                    tardiness = last_scheduled_time_slot - (job.deadline - 1)
                    final_settle -= job.penalty_function.evaluate(tardiness)
        return (
            reward_so_far + final_settle,
            schedule_so_far + [(current_time_slot, None)]
        )
    if available_jobs and current_time_slot == total_time_slots:
        candidate_solutions = []
        for job in available_jobs:
            # suppose we schedule that job at this time slot
            reward_incurred_in_this_time_slot = 0
            # compute reward incurred by this job assignment assumption
            # check if this job is completed at this time slot
            scheduled_time_slots = [time_slot for time_slot, job_id in (schedule_so_far) if job_id == job.id]
            if len(scheduled_time_slots) + 1 == job.processing_time: # job can be completed if we assign it at current_time_slot
                reward_incurred_in_this_time_slot += job.reward
                if current_time_slot > (job.deadline - 1):
                    tardiness = current_time_slot - (job.deadline - 1)
                    reward_incurred_in_this_time_slot -= job.penalty_function.evaluate(tardiness)
            final_settle = 0
            for every_job in job_instances:
                if schedule_counter(every_job.id, schedule_so_far) + (1 if every_job.id == job.id else 0) == 0:
                    # job is not scheduled at all
                    final_settle -= every_job.drop_penalty
                elif schedule_counter(every_job.id, schedule_so_far) + (1 if every_job.id == job.id else 0) < every_job.processing_time:
                    # job is unfinished
                    final_settle -= every_job.drop_penalty
                    # check if job is delayed
                    last_scheduled_time_slot = max(time_slot for time_slot, job_id in (schedule_so_far + [(current_time_slot, job.id)]) if job_id == every_job.id)
                    if every_job.id == job.id:
                        last_scheduled_time_slot = max(last_scheduled_time_slot, current_time_slot)
                    if last_scheduled_time_slot > (every_job.deadline - 1):
                        tardiness = last_scheduled_time_slot - (every_job.deadline - 1)
                        final_settle -= every_job.penalty_function.evaluate(tardiness)
            candidate_solutions.append((
                reward_so_far + reward_incurred_in_this_time_slot + final_settle,
                schedule_so_far + [(current_time_slot, job.id)]
            ))
        # consider the idle time slot as well
        candidate_solutions.append((
            reward_so_far + final_settle,
            schedule_so_far + [(current_time_slot, None)]
        ))
        return max(candidate_solutions, key=lambda x: x[0])