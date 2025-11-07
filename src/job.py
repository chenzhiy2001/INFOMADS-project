from src.penalty_function import PenaltyFunction
import math

class Job:
    '''We consider a single-machine scheduling problem over a discrete
    time horizon {1,2,...,T}, where preemptions are allowed without 
    additional cost.
    
    Each job j is defined by:
    - id (string) unique identifier of the job
    - release_time (integer, > 0)
    - processing_time (integer, > 0)
    - deadline (integer, > release_time) deadline that CAN be exceeded. deadline itself is not schedulable. so if a job has deadline d, it must be completed by time slot d-1 to avoid delay penalty.
    - reward (real, > 0) the reward obtained if the job is completed by its deadline
    - drop_penalty (real, >= 0) the penalty incurred if the job is not completed. In the offline setting, this means that the job is not scheduled at all.
    - penalty_function (object described above) non-decreasing positive function mapping tardiness to penalty incurred
    '''
    def __init__(
            self, 
            id: str,
            release_time: int,
            processing_time: int,
            deadline: int,
            reward: float,
            drop_penalty: float,
            penalty_function: PenaltyFunction
        ):

        assert 0 <= release_time, "Release time must be non-negative."
        assert release_time < deadline, "Release time must be less than deadline."
        assert 0 <= reward, "Reward must be non-negative."
        assert 0 <= drop_penalty, "Drop penalty must be non-negative."
        
        # if not (1 <= release_time < deadline and processing_time > 0):
            # raise ValueError(f"Invalid job parameters for \njob {id}, \nrelease_time: {release_time}, \nprocessing_time: {processing_time}, \ndeadline: {deadline}, \nreward: {reward}, \ndrop_penalty: {drop_penalty}")
        
        self.id = id
        self.release_time = release_time
        self.processing_time = processing_time
        self.deadline = deadline
        self.reward = reward
        self.drop_penalty = drop_penalty
        self.penalty_function = penalty_function
        self.completed = False

        self.t_i_asterisk = None
        if self.penalty_function.function_type == "linear":
            if self.penalty_function.parameters["slope"] > 0: # if it's zero, then the t_i^* = T
                # t_i_asterisk represents maximum acceptable tardiness (delay beyond deadline)
                self.t_i_asterisk = math.floor((self.reward - self.penalty_function.parameters['intercept'])/(self.penalty_function.parameters["slope"]))
        else:
            # For non-linear penalty functions, find the tardiness where penalty exceeds reward
            for tardiness in range(1, len(self.penalty_function.parameters)):
                if self.penalty_function.parameters[tardiness][1] > self.reward:
                    # t_i_asterisk represents maximum acceptable tardiness
                    self.t_i_asterisk = tardiness
                    break

        if self.t_i_asterisk < 0:
            self.t_i_asterisk = 0

    def __str__(self):
        return f"Job(id={self.id}, release_time={self.release_time}, processing_time={self.processing_time}, deadline={self.deadline}, reward={self.reward}, drop_penalty={self.drop_penalty}, penalty_function={self.penalty_function})"

    def __repr__(self):
        return self.__str__()