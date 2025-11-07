# a heuristic to generate an optimal scheduling instance
from math import ceil, floor
import random
from src.job import Job
from src.penalty_function import PenaltyFunction

random.seed(114514)
def generate_random_instance(num_jobs, total_time_slots):
    job_instances = []
    for id in range(num_jobs):
        id = str(id)
        release_time = random.randint(1, total_time_slots) # inclusive
        deadline = random.randint(release_time + 1, total_time_slots + 1) # inclusive
        processing_time = random.randint(1, deadline - release_time)
        reward = (random.random() * 100)
        drop_penalty = (random.random() * 100)
        penalty_slope = (random.random() * 10)
        penalty_intercept = (random.random() * 20)
        penalty_func = PenaltyFunction(function_type="linear", parameters={"slope": penalty_slope, "intercept": penalty_intercept})
        job_instances.append(Job(id, release_time, processing_time, deadline, reward, drop_penalty, penalty_func))
    print(f"Generated {num_jobs} random job instances with total time slots {total_time_slots}.")
    print("Job instances:")
    for job_instance in job_instances:
        print(f"Job ID: {job_instance.id}, Release Time: {job_instance.release_time}, Processing Time: {job_instance.processing_time}, Deadline: {job_instance.deadline}, Reward: {job_instance.reward}, Drop Penalty: {job_instance.drop_penalty}, Penalty Function: slope {job_instance.penalty_function.parameters['slope']}, intercept {job_instance.penalty_function.parameters['intercept']}")
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
