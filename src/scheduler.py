"""
A class to contain the solver for our scheduling problem.
"""
from src.algorithms.ours import OurOffline
from src.job import Job
from src.schedule import Schedule

class Scheduler:
    def __init__(self, name: str, setting: str = "offline"):
        self.name = name
        self.setting = setting

        assert setting in ["offline", "online"], f"Setting must be either 'offline' or 'online'. Got {setting}"

        self.solver = None
    
    
    def setup(self):
        match self.name:
            case "bruteforce":
                self.solver = ...
            case "ours":
                self.solver = OurOffline()
            case _:
                raise ValueError(f"Scheduler {self.name} was not found.")

    def schedule(self, schedule=Schedule) -> Schedule:
        self.solver.schedule(schedule)