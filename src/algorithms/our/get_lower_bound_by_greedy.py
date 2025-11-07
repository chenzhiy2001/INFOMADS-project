from src.schedule import Schedule
from src.job import Job

def lower_bound(schedule: Schedule) -> float:
    # Earliest Completion Time First

    # duplicate the schedule to ensure that we are not modifying the original schedule
    schedule = schedule.copy()

    # reduce the processing time of all the jobs that have been already scheduled
    for job_id in schedule.schedule:
        if job_id is not None:
            job = schedule.get_job_from_id(job_id)
            job.processing_time -= 1

            if job.processing_time <= 0:
                job.completed = True

    t = schedule.T
    while t < schedule.T:

        candidates = schedule.get_candidates()

        # sort the candidates by their processing time (same as deadline here)
        def sort_function(candidate: Job):
            return candidate.processing_time
        candidates.sort(key=sort_function)

        best_candidate: Job = candidates[0]

        for _t in range(t+1, t+best_candidate.processing_time+1):
            schedule.schedule[_t] = best_candidate.id
            best_candidate.completed = True


        schedule.t += best_candidate.processing_time

    # score the schedule
    return schedule.score()





# def get_lower_bound_by_greedy(partial_schedule: Schedule):
#     '''
#     Compute a lower bound for the job assignment by evaluating an instance created by greedy, earliest deadline first (EDF) algorithm.
#     Currently our implementation of EDF is NOT efficient because it unnecessarily re-evaluates available jobs at each time slot. 
#     BUT considering that we may change EDF to other greedy algorithms in the future, we keep this simple and readable implementation for now.
#     '''
#     # compute reward for already FINISHED jobs in partial_schedule. 
#     # Jobs that are halfway done or not yet started are being handled in the next part, 
#     # and those that are not scheduled at all will be handled at the final part of this function.
#     completed_jobs_reward = 0
#     for job_instance in jobs["job_instances"]:
#         if list(partial_schedule["content"].values()).count(job_instance.id) == job_instance.processing_time:
#             # job is finished, check if it's on time or tardy
#             completion_time = max(t for t, job_id in partial_schedule["content"].items() if job_id == job_instance.id)
#             if completion_time <= (job_instance.deadline - 1):
#                 # on time
#                 completed_jobs_reward += job_instance.reward
#             else:
#                 # tardy
#                 tardiness = completion_time - (job_instance.deadline - 1)
#                 tardiness_penalty = job_instance.penalty_function.evaluate(tardiness)
#                 completed_jobs_reward += job_instance.reward - tardiness_penalty
#         elif list(partial_schedule["content"].values()).count(job_instance.id) > job_instance.processing_time:
#             # job is over-finished (should not happen in a valid schedule)
#             raise ValueError(f"Job {job_instance.id} is over-finished.")

#     # compute the reward change from current_timeslot to total_time_slots
#     reward_change = 0
#     # iterate from current_timeslot to total_time_slots to complete the partial schedule
#     for t in range(current_timeslot, jobs["total_time_slots"] + 1):
#         # find the job with the earliest deadline among the available jobs
#         # Get all jobs that can be scheduled in t, i.e., released by (which means before or at) t and not yet finished
#         available_jobs = [
#             job for job in jobs["job_instances"]
#             if job.release_time <= t and list(partial_schedule["content"].values()).count(job.id) < job.processing_time
#         ]
#         if available_jobs:
#             # Sort available jobs by their deadline (earliest deadline first)
#             available_jobs.sort(key=lambda x: x.deadline)
#             # Assign the job with the earliest deadline to the current time slot
#             selected_job = available_jobs[0]
#             partial_schedule["content"][t] = selected_job.id
#             # UPDATE the REWARD CHANGE
#             # Check if the job is completed at this time slot
#             if list(partial_schedule["content"].values()).count(selected_job.id) == selected_job.processing_time:
#                 # Job is completed, check if it's on time or tardy
#                 completion_time = t
#                 if completion_time <= (selected_job.deadline - 1):
#                     reward_change += selected_job.reward
#                 else:
#                     # Calculate tardiness penalty
#                     tardiness = completion_time - (selected_job.deadline - 1)
#                     tardiness_penalty = selected_job.penalty_function.evaluate(tardiness)
#                     reward_change += selected_job.reward - tardiness_penalty

#     completed_jobs_reward += reward_change

#     # final part: compute penalty for unfinished or unscheduled jobs
#     for job_instance in jobs["job_instances"]:
#         if list(partial_schedule["content"].values()).count(job_instance.id) < job_instance.processing_time:
#             # Job is unfinished, apply penalty
#             completed_jobs_reward -= job_instance.drop_penalty

#     return completed_jobs_reward