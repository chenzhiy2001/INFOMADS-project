import json
from src.penalty_function import PenaltyFunction
from src.job import Job

def load_jobs_from_input_file(file_path):
    '''Load jobs from a JSON input file.
    The JSON file should have the following structure:
    ```
    {
        "total_time_slots": 10,
        "jobs": [
            {
                "id": "job1",
                "release_time": 1,
                "processing_time": 2,
                "deadline": 5,
                "reward": 10,
                "drop_penalty": 5,
                "penalty_function": {
                    "function_type": "linear",
                    "parameters": {
                        "slope": 1,
                        "intercept": 0
                    }
                }
            }
        ]
    }
    ```
    total_time_slots denotes how many time slots we have. 
    time slot starts from 1 to total_time_slots, inclusive.
    '''

    with open(file_path, 'r') as f:
        data = json.load(f)

    jobs = {
        "total_time_slots": data["total_time_slots"],
        "job_instances": []
    }
    for job_data in data["jobs"]:
        # Construct penalty function (pf)
        pf_data = job_data["penalty_function"]
        pf = PenaltyFunction(pf_data["function_type"], pf_data["parameters"])
        # make sure each job's release time and deadline are within total_time_slots
        if not (1 <= job_data["release_time"] < job_data["deadline"] <= (data["total_time_slots"] + 1 )): # deadline itself is not schedulable
            raise ValueError(f"Job {job_data['id']} has illegal release time {job_data['release_time']} or deadline {job_data['deadline']}. total time slots: {data['total_time_slots']}.")
        job_instance = Job(
            id=job_data["id"],
            release_time=job_data["release_time"],
            processing_time=job_data["processing_time"],
            deadline=job_data["deadline"],
            reward=job_data["reward"],
            drop_penalty=job_data["drop_penalty"],
            penalty_function=pf
        )
        jobs["job_instances"].append(job_instance)
    
    return jobs
