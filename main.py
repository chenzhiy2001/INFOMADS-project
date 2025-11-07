import json
import copy
from src.penalty_function import PenaltyFunction
from src.job import Job
# from src.get_lower_bound_by_greedy import get_lower_bound_by_greedy
# from src.get_upper_bound_by_LP import get_upper_bound_by_LP
# from test_instances import generate_random_instance
# from src.bruteforce import bruteforce_schedule, schedule_counter
from fire import Fire
from src.utility import load_jobs_from_input_file, display_schedule, load_solution
from src.scheduler import Scheduler
from typing import Optional
from src.schedule import Schedule

def main(file: str, name: str = 'ours', setting: str = 'offline', solution: Optional[str] = None, output_path: Optional[str] = None):
    # runtime : compare between bruteforce and infomads
    # online: existing work vs infomads
    # offline: bruteforce vs infomads

    # schedule = load_jobs_from_input_file("input.json")
    # schedule = load_jobs_from_input_file("input.txt")
    schedule: Schedule = load_jobs_from_input_file(file)

    if solution is not None:
        schedule = load_solution(solution, schedule)
    else:
        # print(schedule)
        scheduler = Scheduler(name, setting)
        schedule = scheduler.schedule(schedule)
    
    if output_path is not None:
        schedule.export(output_path)
    else:
        print(f"Schedule found with score: {schedule.score()}")
        display_schedule(schedule)

    


if __name__ == "__main__":
    Fire(main)
