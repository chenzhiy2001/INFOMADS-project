class job:
    '''We consider a single-machine scheduling problem over a discrete
    time horizon {1,2,...,T}, where preemptions are allowed without 
    additional cost.
    
    Each job j is defined by:
    - id (string) unique identifier of the job
    - release_time (integer, > 0)
    - processing_time (integer, > 0)
    - deadline (integer, > release_time) deadline that CAN be exceeded
    - reward (real, > 0) the reward obtained if the job is completed by its deadline
    - drop_penalty (real, >= 0) the penalty incurred if the job is not completed. In the offline setting, this means that the job is not scheduled at all.
    - penalty_function (object described above) non-decreasing positive function mapping tardiness to penalty incurred
    '''
    def __init__(self, id, release_time, processing_time, deadline, reward, drop_penalty, penalty_function):
        # make sure 1 <= release_time < deadline and processing_time > 0
        if not (1 <= release_time < deadline and processing_time > 0):
            raise ValueError(f"Invalid job parameters for \njob {id}, \nrelease_time: {release_time}, \nprocessing_time: {processing_time}, \ndeadline: {deadline}, \nreward: {reward}, \ndrop_penalty: {drop_penalty}")
        self.id = id
        self.release_time = release_time
        self.processing_time = processing_time
        self.deadline = deadline
        self.reward = reward
        self.drop_penalty = drop_penalty
        self.penalty_function = penalty_function