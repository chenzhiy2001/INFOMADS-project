import sched
from src.algorithms.base import BaseOfflineSolver
from src.schedule import Schedule

from src.job import Job


class OurOnline(BaseOfflineSolver):
    def __init__(self):
        super().__init__()

    def c_i(self, t: int, job: Job) -> float:
        if t + job.processing_time >= job.deadline + 1:
            return job.penalty_function.evaluate(t - job.deadline + job.processing_time)
        else:
            return 0

    def u_i(self, t: int, job: Job) -> float:
        return (job.reward - self.c_i(t, job)) / job.processing_time

    def schedule(self, schedule: Schedule) -> Schedule:
        
        # assume schedule.t == -1

        while schedule.t < schedule.T:
            schedule.t += 1

            candidates = schedule.schedulable_jobs(schedule.t)
            
            if len(candidates) == 0:
                continue
            
            uis = [(self.u_i(schedule.t, job), job) for job in candidates]
            # sort 
            uis.sort(key=lambda x: x[0])

            u_i, job = uis[0]
            schedule.schedule[schedule.t] = job.id

            if sum(1 for job_id in schedule.schedule if job_id == job.id) >= job.processing_time:
                job.completed = True

        return schedule