from math import floor


def schedule_counter(job_id, schedule_so_far):
    count = 0
    for time_slot, scheduled_job_id in schedule_so_far:
        if scheduled_job_id == job_id:
            count += 1
    return count

def online_schedule(current_time_slot, job_instances, total_time_slots, reward_so_far, schedule_so_far, alternative_u=None):

    def c(job, current_time_slot):
        if current_time_slot + job.processing_time >= job.deadline + 1:
            return job.penalty_function.evaluate(current_time_slot - job.deadline + job.processing_time)
        else:
            return 0

    def u(job, current_timeslots):
        return (job.reward - c(job, current_timeslots)) / job.processing_time
    
    if alternative_u is not None:
        u = alternative_u
    
    # t_i_asterisk is the last time step (so they are integers) by which the penalty of pushing the job back by t_i_asterisk time slots does NOT exceeds the reward of job i
    t_i_asterisk = {}
    for job_instance in job_instances:
        slope = job_instance.penalty_function.parameters["slope"]
        intercept = job_instance.penalty_function.parameters["intercept"]
        if slope == 0:
            # penalty is constant, so t_i_asterisk is the final time slot
            t_i_asterisk[job_instance.id] = job_instance.total_time_slots
        else:
            t_i_asterisk_value = floor((job_instance.reward - intercept) / slope) # round down to nearest integer, which make sense because we want the LAST time step that is still WITHIN the reward
            if t_i_asterisk_value < 0:
                t_i_asterisk[job_instance.id] = 0
            else:
                t_i_asterisk[job_instance.id] = t_i_asterisk_value

    # get all available jobs at this time slot
    available_jobs = []
    for job in job_instances:
        # this definition is different from bruteforce: we only consider jobs in [release time, make-sense deadline)
        if job.release_time <= current_time_slot and current_time_slot < job.deadline + t_i_asterisk[job.id] - job.processing_time:
            available_jobs.append(job)

    best_job = None
    best_u_value = float("-inf")

    for job in available_jobs:
        u_value = u(job, current_time_slot)
        if u_value > best_u_value:
            best_u_value = u_value
            best_job = job

    if not available_jobs and current_time_slot < total_time_slots:
        return (reward_so_far, schedule_so_far + (current_time_slot, None))
    
    if available_jobs and current_time_slot < total_time_slots:
        # suppose we schedule that job at this time slot
        reward_incurred_in_this_time_slot = 0
        # compute reward incurred by this job assignment assumption
        # check if this job is completed at this time slot
        scheduled_time_slots = [time_slot for time_slot, job_id in enumerate(schedule_so_far) if job_id == best_job.id]
        if len(scheduled_time_slots) + 1 == best_job.processing_time: # job can be completed if we assign it at current_time_slot
            reward_incurred_in_this_time_slot += best_job.reward
            if current_time_slot > (best_job.deadline - 1):
                tardiness = current_time_slot - (best_job.deadline - 1)
                reward_incurred_in_this_time_slot -= best_job.penalty_function.evaluate(tardiness)
        return (reward_so_far + reward_incurred_in_this_time_slot,
                schedule_so_far + (current_time_slot, best_job.id))
    
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
                last_scheduled_time_slot = max(time_slot for time_slot, job_id in enumerate(schedule_so_far) if job_id == job.id)
                if last_scheduled_time_slot > (job.deadline - 1):
                    tardiness = last_scheduled_time_slot - (job.deadline - 1)
                    final_settle -= job.penalty_function.evaluate(tardiness)
        return (
            reward_so_far + final_settle,
            schedule_so_far + (current_time_slot, None)
        )
    if available_jobs and current_time_slot == total_time_slots:
        reward_incurred_in_this_time_slot = 0
        scheduled_time_slots = [time_slot for time_slot, job_id in enumerate(schedule_so_far) if job_id == best_job.id]
        if len(scheduled_time_slots) + 1 == best_job.processing_time: # job can be completed if we assign it at current_time_slot
            reward_incurred_in_this_time_slot += best_job.reward
            if current_time_slot > (best_job.deadline - 1):
                tardiness = current_time_slot - (best_job.deadline - 1)
                reward_incurred_in_this_time_slot -= best_job.penalty_function.evaluate(tardiness)
        final_settle = 0
        for job in job_instances:
            if schedule_counter(job.id, schedule_so_far) + (1 if job.id == best_job.id else 0) == 0:
                # job is not scheduled at all
                final_settle -= job.drop_penalty
            elif schedule_counter(job.id, schedule_so_far) + (1 if job.id == best_job.id else 0) < job.processing_time:
                # job is unfinished
                final_settle -= job.drop_penalty
                # check if job is delayed
                last_scheduled_time_slot = max(time_slot for time_slot, job_id in enumerate(schedule_so_far) if job_id == job.id)
                if job.id == best_job.id:
                    last_scheduled_time_slot = max(last_scheduled_time_slot, current_time_slot)
                if last_scheduled_time_slot > (job.deadline - 1):
                    tardiness = last_scheduled_time_slot - (job.deadline - 1)
                    final_settle -= job.penalty_function.evaluate(tardiness)
        return (
            reward_so_far + reward_incurred_in_this_time_slot + final_settle,
            schedule_so_far + (current_time_slot, best_job.id)
        )

    
