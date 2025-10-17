import json

class penalty_function:
    '''A penalty function is defined by:
    - a string of function type: "per-timeslot", "linear"
    - an object defining the function parameters:
      - "per-timeslot": a list of (time, penalty) points, can be used to define step-wise functions
      - "linear": a slope (real number) and an intercept (real number)
    '''
    def __init__(self, function_type, parameters):
        self.function_type = function_type
        if function_type not in ["per-timeslot", "linear"]:
            raise ValueError("Invalid function type. Must be 'per-timeslot' or 'linear'.")
        elif function_type == "per-timeslot":
            if not isinstance(parameters, list):
                raise ValueError("Parameters for 'per-timeslot' must be a list of (time, penalty) points.")
            for point in parameters:
                if not (isinstance(point, tuple) and len(point) == 2 and isinstance(point[0], int) and isinstance(point[1], (int, float))):
                    raise ValueError("Each point must be a tuple of (time (int), penalty (real)).")
                # Ensure non-decreasing positive function
                if point[0] < 1 or point[1] < 0:
                    raise ValueError("Time must be positive and penalty values must be non-negative.")
        elif function_type == "linear":
            if not (isinstance(parameters, dict) and "slope" in parameters and "intercept" in parameters):
                raise ValueError("Parameters for 'linear' must be a dict with 'slope' and 'intercept'.")
            if not (isinstance(parameters["slope"], (int, float)) and isinstance(parameters["intercept"], (int, float))):
                raise ValueError("'slope' and 'intercept' must be real numbers.")
            # Ensure non-decreasing positive function
            if parameters["slope"] < 0:
                raise ValueError("Slope must be non-negative for a non-decreasing function.")
            if parameters["intercept"] < 0:
                raise ValueError("Intercept must be non-negative.")
        self.parameters = parameters


class job:
    '''We consider a single-machine scheduling problem over a discrete
    time horizon {1,2,...,T}, where preemptions are allowed without 
    additional cost.
    
    Each job j is defined by:
    - id (string) unique identifier of the job
    - release_time (integer, > 0)
    - processing_time (integer, > 0)
    - deadline (integer, > release_time)
    - reward (real, > 0) the reward obtained if the job is completed by its deadline
    - drop_penalty (real, >= 0) the penalty incurred if the job is not completed. In the offline setting, this means that the job is not scheduled at all.
    - penalty_function (object described above) non-decreasing positive function mapping tardiness to penalty incurred
    '''
    def __init__(self, id, release_time, processing_time, deadline, reward, drop_penalty, penalty_function):
        self.id = id
        self.release_time = release_time
        self.processing_time = processing_time
        self.deadline = deadline
        self.reward = reward
        self.drop_penalty = drop_penalty
        self.penalty_function = penalty_function

def load_jobs_from_input_file(file_path):
    
    with open(file_path, 'r') as f:
        data = json.load(f)

    jobs = []
    for job_data in data["jobs"]:
        # Construct penalty function
        pf_data = job_data["penalty_function"]
        pf = penalty_function(pf_data["function_type"], pf_data["parameters"])
        job_instance = job(
            id=job_data["id"],
            release_time=job_data["release_time"],
            processing_time=job_data["processing_time"],
            deadline=job_data["deadline"],
            reward=job_data["reward"],
            drop_penalty=job_data["drop_penalty"],
            penalty_function=pf
        )
        jobs.append(job_instance)
    
    return jobs


def main():
    jobs = load_jobs_from_input_file("input.json")
    print("Hello from infomads-project!")
    for job in jobs:
        print(f"Loaded job: {job.id}")


if __name__ == "__main__":
    main()
