import json
import copy
from penalty_function import penalty_function
from job import job
from get_lower_bound_by_greedy import get_lower_bound_by_greedy
from get_upper_bound_by_LP import get_upper_bound_by_LP
from test_instances import generate_random_instance
from bruteforce import bruteforce_schedule, schedule_counter

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
        pf = penalty_function(pf_data["function_type"], pf_data["parameters"])
        # make sure each job's release time and deadline are within total_time_slots
        if not (1 <= job_data["release_time"] < job_data["deadline"] <= (data["total_time_slots"] + 1 )): # deadline itself is not schedulable
            raise ValueError(f"Job {job_data['id']} has illegal release time {job_data['release_time']} or deadline {job_data['deadline']}. total time slots: {data['total_time_slots']}.")
        job_instance = job(
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


def schedule_jobs(jobs):
    '''
    - For each time slot, we will determine the lower and upper bounds for the job assignment of the current time slot.
      - Lower bound is computed by a greedy algorithm.
      - Upper bound is computed by solving a MILP formulation of the scheduling problem with an assumption of current job assignment.
    - Then we will do branch-and-bound to find the optimal job assignment for current time slot.
    '''
    # we define partial_schedule as a dictionary mapping time slot to job id assigned at that time slot.
    root_partial_schedule = {
        "id": 0,
        "content": {}, 
        "lower_bound": float('-inf'),
        "upper_bound": float('inf'),
        "parent_id": None,
        "children_ids": []
    }
    # since there are frequent backtracks to update ancestor nodes' bounds, we will maintain the branch-and-bound tree instead of just a queue of partial schedules.
    branch_and_bound_tree = {}
    # the way to add a new partial schedule to the tree
    branch_and_bound_tree[root_partial_schedule["id"]] = root_partial_schedule

    # we start expanding the tree starting from time slot 1
    current_timeslot = 1
    # start from the root node
    BFS_queue = [branch_and_bound_tree[0]]
    deleted_nodes = []
    # solutions where lower bound == upper bound
    optimal_solutions = [] # todo
    while BFS_queue:
        partial_schedule = BFS_queue.pop(0)
        # examine all "child nodes" (partial schedules) at the current time slot
        for job_instance in jobs["job_instances"]:
            # start by ditching infeasible children nodes
            # if the job is already finished, skip it. Be careful that one value in partial_schedule corresponds to one time slot, so job_instance.id in partial_schedule["content"].values() does not necessarily mean the job is finished.
            if list(partial_schedule["content"].values()).count(job_instance.id) == job_instance.processing_time:
                continue
            elif list(partial_schedule["content"].values()).count(job_instance.id) > job_instance.processing_time:
                raise ValueError(f"Job {job_instance.id} has been assigned more time slots than its processing time.")
            # if the job is not yet released, skip it
            if current_timeslot < job_instance.release_time:
                continue
            # Now we are sure that this job assignment at this timeslot is feasible, assume we assign this job to the current time slot
            # use object DEEP COPY to avoid modifying the original partial_schedule
            partial_schedule_assumption = copy.deepcopy(partial_schedule)
            partial_schedule_assumption["content"][current_timeslot] = job_instance.id
            current_timeslot_assumption = current_timeslot + 1
            if current_timeslot < jobs["total_time_slots"]:
                lower_bound_for_this_assumption = get_lower_bound_by_greedy(partial_schedule_assumption, current_timeslot_assumption, jobs)
                upper_bound_for_this_assumption = get_upper_bound_by_LP(partial_schedule_assumption, current_timeslot_assumption, jobs)
                # first we add the new schedule to branch_and_bound_tree
                new_partial_schedule_id = len(branch_and_bound_tree)
                new_partial_schedule = {
                    "id": new_partial_schedule_id,
                    "content": partial_schedule_assumption["content"], 
                    "lower_bound": lower_bound_for_this_assumption,
                    "upper_bound": upper_bound_for_this_assumption,
                    "parent_id": partial_schedule["id"],
                    "children_ids": []
                }
                branch_and_bound_tree[new_partial_schedule_id] = new_partial_schedule
                branch_and_bound_tree[partial_schedule["id"]]["children_ids"].append(new_partial_schedule_id)
                # then we decide whether to add this new schedule to BFS queue for FURTHER expansion
                if lower_bound_for_this_assumption < upper_bound_for_this_assumption:  # add to BFS queue for further expansion
                    BFS_queue.append(new_partial_schedule)
                elif lower_bound_for_this_assumption == upper_bound_for_this_assumption:  # found optimal solution for this branch, can stop expanding further
                    pass
                else:
                    raise ValueError("Lower bound exceeds upper bound, which should not happen.")
            elif current_timeslot == jobs["total_time_slots"]:  # last time slot, no need to compute bounds for next time slot
                # calculate the exact reward for this complete schedule
                final_reward = get_lower_bound_by_greedy(partial_schedule_assumption, current_timeslot_assumption, jobs) # in this case, current_timeslot_assumption = total_time_slots + 1, so it exceeds total time slots
                # we add the new schedule to branch_and_bound_tree
                new_partial_schedule_id = len(branch_and_bound_tree)
                new_partial_schedule = {
                    "id": new_partial_schedule_id,
                    "content": partial_schedule_assumption["content"], 
                    "lower_bound": final_reward,
                    "upper_bound": final_reward,
                    "parent_id": partial_schedule["id"],
                    "children_ids": []
                }
                branch_and_bound_tree[new_partial_schedule_id] = new_partial_schedule
                branch_and_bound_tree[partial_schedule["id"]]["children_ids"].append(new_partial_schedule_id)
                # no need to add to BFS queue since this is the last time slot
            else:
                raise ValueError("Current time slot exceeds total time slots, which should not happen.")
        # after examining all child nodes (aka all possible, feasible job assignments) at the current time slot, we need to backtrack to update ancestor nodes' bounds
        # we do this by traversing up the tree from the current partial_schedule to the root
        update_range_node = partial_schedule
        while True:
            # only update if there are children nodes
            if update_range_node["children_ids"]:
                # update parent's lower bound and upper bound
                child_lower_bounds = [branch_and_bound_tree[child_id]["lower_bound"] for child_id in update_range_node["children_ids"]]
                child_upper_bounds = [branch_and_bound_tree[child_id]["upper_bound"] for child_id in update_range_node["children_ids"]]
                # new lower bound is the MAXIMUM of children's lower bounds and parent's lower bound
                update_range_node["lower_bound"] = max(child_lower_bounds + [update_range_node["lower_bound"]])
                # new upper bound is the biggest amongst those that are >= parent's new lower bound, NOT including parent's old upper bound
                update_range_node["upper_bound"] = max(ub for ub in child_upper_bounds if ub >= update_range_node["lower_bound"])
                # before moving up we need to do 2 things
                for child_id in update_range_node["children_ids"]:
                    # 1. delete some branches whose upper bound < parent's new lower bound
                    if branch_and_bound_tree[child_id]["upper_bound"] < update_range_node["lower_bound"]:
                        # remove this child id from parent's children_ids so it's not reachable in the tree anymore
                        update_range_node["children_ids"].remove(child_id)
                        # add this child id to deleted_nodes for record
                        deleted_nodes.append(child_id)
                    # 2. record optimal solutions where lower bound == upper bound
                    if branch_and_bound_tree[child_id]["lower_bound"] == branch_and_bound_tree[child_id]["upper_bound"]:
                        optimal_solutions.append(branch_and_bound_tree[child_id])
            # move up to parent
            if update_range_node["parent_id"] is not None:
                update_range_node = branch_and_bound_tree[update_range_node["parent_id"]]
            else:
                break
    return optimal_solutions

def main():
    # runtime : compare between bruteforce and infomads
    # online: existing work vs infomads
    # offline: bruteforce vs infomads

    # jobs = load_jobs_from_input_file("input.json")
    jobs = generate_random_instance(num_jobs=5, total_time_slots=5)
    output = schedule_jobs(jobs)
    print("Optimal schedules found:")
    for schedule in output:
        print(schedule)
    bruteforce_schedule_output = bruteforce_schedule(
        current_time_slot=1,
        job_instances=jobs["job_instances"],
        total_time_slots=jobs["total_time_slots"],
        reward_so_far=0,
        schedule_so_far=[]
    )
    print("Bruteforce schedule output:")
    print(bruteforce_schedule_output)
    


if __name__ == "__main__":
    main()
