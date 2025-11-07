from src.job import Job
import copy

class Schedule:
    def __init__(self, jobs: list[Job], total_time_slots: int):
        self.jobs = jobs
        self.T = total_time_slots
        self.schedule = [None] * self.T

        # update each job's t_i_asterisk
        for job in self.jobs:
            if job.t_i_asterisk == None:
                job.t_i_asterisk = self.T
        
        self.t = 0

    def schedulable_jobs(self, time_step: int) -> list[Job]:
        return [
            job for job in self.jobs
            if (time_step > job.release_time) and (time_step < job.deadline + job.t_i_asterisk) and job.completed == False
        ]

    def copy(self) -> 'Schedule':
        return copy.deepcopy(self)

    def score(self) -> float:
        _score = 0
        for job in self.jobs:
            scheduled = sum(1 for job_id in self.schedule if job_id == job.id)

            if scheduled >= job.processing_time:
                _score += job.reward  # + job.penalty?

                # if the 
