from src.job import Job
import copy

from typing import List
from typing import Optional

class Schedule:
    def __init__(self, jobs: list[Job], total_time_slots: int):
        self.jobs: List[Job] = jobs
        self.T = total_time_slots
        self.schedule: List[Optional[Job]] = [None] * self.T

        # update each job's t_i_asterisk
        for job in self.jobs:
            if job.t_i_asterisk == None:
                job.t_i_asterisk = self.T
        
        # print([job.t_i_asterisk for job in self.jobs])
        
        # current time step
        self.t = -1

        self.upper_bound = None
        self.lower_bound = None

    def schedulable_jobs(self, time_step: int) -> list[Job]:
        # t_i_asterisk represents maximum acceptable tardiness
        # Job can be scheduled if: release_time <= time_step < deadline + t_i_asterisk
        return [
            job for job in self.jobs
            if (time_step >= job.release_time) and (time_step < job.deadline + job.t_i_asterisk) and (job.completed == False)
        ]

    def get_candidates(self) -> list['Schedule']:
        """
        Returns all possible schedules that schedules all possible jobs at the given time step
        """

        candidates = []
        
        # Check if we've already scheduled all time slots (t+1 would be out of bounds)
        # When t == T-1, we've scheduled all T time slots (indices 0 to T-1)
        if self.t >= self.T - 1:
            return candidates
        
        schedulable = self.schedulable_jobs(self.t+1)
        if len(schedulable) == 0:
            # schedule null (no job at this time slot)
            candidate = self.copy()
            candidate.schedule[self.t + 1] = None
            candidate.t = self.t + 1
            candidate.upper_bound = None
            candidate.lower_bound = None
            candidates.append(candidate)
            
            return candidates
        

        for job in schedulable:
            candidate = self.copy()
            candidate.schedule[self.t + 1] = job.id
            candidate.t = self.t + 1
            candidate.upper_bound = None
            candidate.lower_bound = None

            # Mark job as completed in the candidate if it has been fully scheduled
            candidate_job = candidate.get_job_from_id(job.id)
            number_of_scheduled_steps = sum(1 for job_id in candidate.schedule if job_id == job.id)
            if number_of_scheduled_steps == candidate_job.processing_time:
                candidate_job.completed = True

            candidates.append(candidate)

        return candidates


    def copy(self) -> 'Schedule':
        # Create a new Schedule instance with deep-copied jobs
        jobs_copy = [copy.deepcopy(job) for job in self.jobs]
        new_schedule = Schedule(jobs_copy, self.T)
        new_schedule.schedule = list(self.schedule)
        new_schedule.t = self.t
        new_schedule.upper_bound = self.upper_bound
        new_schedule.lower_bound = self.lower_bound
        return new_schedule

    def get_job_from_id(self, job_id) -> Job:
        for job in self.jobs:
            if job.id == job_id:
                return job
        raise RuntimeError(f"Job with id {job_id} not found in jobs ({self.jobs})")

    def score(self) -> float:
        _score = 0
        for job in self.jobs:
            if job.completed:
                _score += job.reward
                
                latest_completion_time = max(t for t, job_id in enumerate(self.schedule) if job_id == job.id)
                if latest_completion_time > job.deadline:
                    tardiness = latest_completion_time - job.deadline
                    _score -= job.penalty_function.evaluate(tardiness)

            else:
                _score -= job.drop_penalty

        return _score

    def export(self, path: str):
        with open(path, 'w') as file:
            for job in self.jobs:
                scheduled_times_slots = [t for t, job_id in enumerate(self.schedule) if job_id == job.id]
                if len(scheduled_times_slots) == 0:
                    file.write('null\n')
                else:
                    file.write(', '.join([t+1 for t in scheduled_times_slots]) + '\n')
            file.write(f'{self.score()}\n')