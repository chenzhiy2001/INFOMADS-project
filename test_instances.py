# a heuristic to generate an optimal scheduling instance
from math import ceil
from random import random
from job import job
from penalty_function import penalty_function

def generate_random_instance(num_jobs, total_time_slots):
    job_instances = []
    for id in range(num_jobs):
        id = str(id)
        release_time = ceil(random() * (total_time_slots))
        deadline = release_time + ceil(random() * (total_time_slots - release_time))
        processing_time = ceil(random() * (deadline - release_time))
        reward = (random() * 100)
        drop_penalty = (random() * 100)
        penalty_slope = random() * 10
        penalty_intercept = random() * 20
        penalty_func = penalty_function(function_type="linear", parameters={"slope": penalty_slope, "intercept": penalty_intercept})
        job_instances.append(job(id, release_time, processing_time, deadline, reward, drop_penalty, penalty_func))
    return {
        "total_time_slots": total_time_slots,
        "job_instances": job_instances
    }





# since getting an optimal scheduling instance for a random instance is usually exponential,
# we will generate the optimal scheduling and job description together, gradually.
# this is unfinished because it's fucking annoying to implement.
def generate_optimal_instance_heuristic(num_jobs, total_time_slots):
    # we generate job rewards and penalty functions first
    # then generate the scheduling based on the maximal reward, penalty function set.

    # generate 1 random job reward and a random linear job penalty function
    def generate_random_job():
        reward = ceil(random() * 100)
        penalty_slope = random() * 10
        penalty_intercept = random() * 20
        penalty_func = penalty_function.linear_penalty_function(penalty_slope, penalty_intercept)
        return (reward, penalty_func)
    
    # generate another job. in the following scheduling-generation step we will ensure that
    # this job's scheduling must be interrupted by the first job, forcing it to delay and incur delay penalty.
    return 'bruh'
