import json
import copy
from src.penalty_function import PenaltyFunction
from src.job import Job
# from src.get_lower_bound_by_greedy import get_lower_bound_by_greedy
# from src.get_upper_bound_by_LP import get_upper_bound_by_LP
from test_instances import generate_random_instance
# from src.bruteforce import bruteforce_schedule, schedule_counter
from fire import Fire
from src.utility import load_jobs_from_input_file, display_schedule
from src.scheduler import Scheduler

def main(name: str = 'ours', setting: str = 'offline'):
    # runtime : compare between bruteforce and infomads
    # online: existing work vs infomads
    # offline: bruteforce vs infomads

    schedule = load_jobs_from_input_file("input.json")
    scheduler = Scheduler(name, setting)
    schedule = scheduler.schedule(schedule)
    
    print(f"Schedule found with score: {schedule.score()}")
    display_schedule(schedule)

    
    # jobs = generate_random_instance(num_jobs=5, total_time_slots=5)
    # optimal_schedules, branch_reports = schedule_jobs(jobs)
    # print("Branch-and-bound trace:")
    # for report in branch_reports:
    #     print(report)
    # print("Optimal schedules found:")
    # for schedule in optimal_schedules:
    #     print(schedule)
    # bruteforce_schedule_output = bruteforce_schedule(
    #     current_time_slot=1,
    #     job_instances=jobs["job_instances"],
    #     total_time_slots=jobs["total_time_slots"],
    #     reward_so_far=0,
    #     schedule_so_far=[]
    # )
    # print("Bruteforce schedule output:")
    # print(bruteforce_schedule_output)
    


if __name__ == "__main__":
    Fire(main)
