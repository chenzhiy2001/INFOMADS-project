import unittest
from src.utility import load_solution
from src.schedule import Schedule
from src.job import Job
from src.penalty_function import PenaltyFunction
from src.utility import load_jobs_from_input_file, load_solution
from src.scheduler import Scheduler


class TestStringMethods(unittest.TestCase):
    # def test_schedule_1(self):
    #     path_jobs = 'tests/Job-1.txt'
    #     path_solution = 'tests/Schedule-1.txt'

    #     # schedule the jobs
    #     schedule_jobs = load_jobs_from_input_file(path_jobs)
    #     schedule_solution = schedule_jobs.copy()

    #     scheduler = Scheduler('ours', 'offline')
    #     schedule_jobs = scheduler.schedule(schedule_jobs)

    #     schedule_solution = load_solution(path_solution, schedule_solution)

    #     self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} where as optimal is {schedule_solution.score()}")
        
    # def test_schedule_2(self):
    #     path_jobs = 'tests/Job-2.txt'
    #     path_solution = 'tests/Schedule-2.txt'

    #     # schedule the jobs
    #     schedule_jobs = load_jobs_from_input_file(path_jobs)
    #     schedule_solution = schedule_jobs.copy()

    #     scheduler = Scheduler('ours', 'offline')
    #     schedule_jobs = scheduler.schedule(schedule_jobs)

    #     schedule_solution = load_solution(path_solution, schedule_solution)

    #     self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} where as optimal is {schedule_solution.score()}")
        
    def test_schedule_3(self):
        path_jobs = 'tests/Job-3.txt'
        path_solution = 'tests/Schedule-3.txt'

        # schedule the jobs
        schedule_jobs = load_jobs_from_input_file(path_jobs)
        schedule_solution = schedule_jobs.copy()

        scheduler = Scheduler('ours', 'offline')
        schedule_jobs = scheduler.schedule(schedule_jobs)

        schedule_solution = load_solution(path_solution, schedule_solution)

        self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} whereas optimal is {schedule_solution.score()}")

    def test_schedule_4(self):
        path_jobs = 'tests/Job-4.txt'
        path_solution = 'tests/Schedule-4.txt'

        # schedule the jobs
        schedule_jobs = load_jobs_from_input_file(path_jobs)
        schedule_solution = schedule_jobs.copy()

        scheduler = Scheduler('ours', 'offline')
        schedule_jobs = scheduler.schedule(schedule_jobs)

        schedule_solution = load_solution(path_solution, schedule_solution)

        self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} whereas optimal is {schedule_solution.score()}")

    # def test_schedule_5(self):
    #     path_jobs = 'tests/Job-5.txt'
    #     path_solution = 'tests/Schedule-5.txt'

    #     # schedule the jobs
    #     schedule_jobs = load_jobs_from_input_file(path_jobs)
    #     schedule_solution = schedule_jobs.copy()

    #     scheduler = Scheduler('ours', 'offline')
    #     schedule_jobs = scheduler.schedule(schedule_jobs)

    #     schedule_solution = load_solution(path_solution, schedule_solution)

    #     self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} whereas optimal is {schedule_solution.score()}")

    def test_schedule_6(self):
        path_jobs = 'tests/Job-6.txt'
        path_solution = 'tests/Schedule-6.txt'

        # schedule the jobs
        schedule_jobs = load_jobs_from_input_file(path_jobs)
        schedule_solution = schedule_jobs.copy()

        scheduler = Scheduler('ours', 'offline')
        schedule_jobs = scheduler.schedule(schedule_jobs)

        schedule_solution = load_solution(path_solution, schedule_solution)

        self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} whereas optimal is {schedule_solution.score()}")

    def test_schedule_7(self):
        path_jobs = 'tests/Job-7.txt'
        path_solution = 'tests/Schedule-7.txt'

        # schedule the jobs
        schedule_jobs = load_jobs_from_input_file(path_jobs)
        schedule_solution = schedule_jobs.copy()

        scheduler = Scheduler('ours', 'offline')
        schedule_jobs = scheduler.schedule(schedule_jobs)

        schedule_solution = load_solution(path_solution, schedule_solution)

        self.assertEqual(schedule_jobs.score(), schedule_solution.score(), f"Got {schedule_jobs.score()} whereas optimal is {schedule_solution.score()}")

if __name__ == '__main__':
    unittest.main()
