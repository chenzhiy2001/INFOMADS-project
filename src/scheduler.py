"""
A class to contain the solver for our scheduling problem.
"""
from src.algorithms.ours_offline import OurOffline
from src.algorithms.ours_online import OurOnline
from src.job import Job
from src.schedule import Schedule

class Scheduler:
    def __init__(self, name: str, setting: str = "offline"):
        self.name = name
        self.setting = setting

        assert setting in ["offline", "online"], f"Setting must be either 'offline' or 'online'. Got {setting}"

        self.solver = None

        self.setup()
    
    
    def setup(self):
        match self.name:
            case "bruteforce":
                raise NotImplementedError("Bruteforce solver is not implemented yet")
                self.solver = ...
            case "ours":
                if self.setting == 'offline':
                    self.solver = OurOffline()
                elif self.setting == 'online':
                    self.solver = OurOnline()
                else:
                    raise ValueError(f"Setting must be either 'offline' or 'online'. Got {self.setting}")
            case _:
                raise ValueError(f"Scheduler {self.name} was not found.")

    def schedule(self, schedule=Schedule) -> Schedule:
        return self.solver.schedule(schedule)