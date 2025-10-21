import json
from shutil import copy
# scipy for MILP
from scipy.optimize import linprog
from penalty_function import penalty_function
from job import job

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
        if not (1 <= job_data["release_time"] < job_data["deadline"] <= data["total_time_slots"]):
            raise ValueError(f"Job {job_data['id']}'s release time and deadline must be within [1,{data['total_time_slots']}(total_time_slots)].")
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


def get_lower_bound_by_greedy(partial_schedule, current_timeslot, jobs):
    '''
    Compute a lower bound for the job assignment by evaluating an instance created by greedy, earliest deadline first (EDF) algorithm.
    Currently our implementation of EDF is NOT efficient because it unnecessarily re-evaluates available jobs at each time slot. BUT considering that we may change EDF to other greedy algorithms in the future, we keep this simple and readable implementation for now.
    '''
    # compute reward for already FINISHED jobs in partial_schedule. Jobs that are halfway done or not yet started are being handled in the next part, and those that are not scheduled at all will be handled at the final part of this function.
    completed_jobs_reward = 0
    for job_instance in jobs.job_instances:
        if list(partial_schedule["content"].values()).count(job_instance.id) == job_instance.processing_time:
            # job is finished, check if it's on time or tardy
            completion_time = max(t for t, job_id in partial_schedule["content"].items() if job_id == job_instance.id)
            if completion_time <= job_instance.deadline:
                # on time
                completed_jobs_reward += job_instance.reward
            else:
                # tardy
                tardiness = completion_time - job_instance.deadline
                tardiness_penalty = job_instance.penalty_function.evaluate(tardiness)
                completed_jobs_reward += job_instance.reward - tardiness_penalty
        elif list(partial_schedule["content"].values()).count(job_instance.id) > job_instance.processing_time:
            # job is over-finished (should not happen in a valid schedule)
            raise ValueError(f"Job {job_instance.id} is over-finished.")

    # compute the reward change from current_timeslot to total_time_slots
    reward_change = 0
    # iterate from current_timeslot to total_time_slots to complete the partial schedule
    for t in range(current_timeslot, jobs.total_time_slots + 1):
        # find the job with the earliest deadline among the available jobs
        # Get all jobs that can be scheduled in t, i.e., released by (which means before or at) t and not yet finished
        available_jobs = [
            job for job in jobs.job_instances
            if job.release_time <= t and list(partial_schedule["content"].values()).count(job.id) < job.processing_time
        ]
        if available_jobs:
            # Sort available jobs by their deadline (earliest deadline first)
            available_jobs.sort(key=lambda x: x.deadline)
            # Assign the job with the earliest deadline to the current time slot
            selected_job = available_jobs[0]
            partial_schedule["content"][t] = selected_job.id
            # UPDATE the REWARD CHANGE
            # Check if the job is completed at this time slot
            if list(partial_schedule["content"].values()).count(selected_job.id) == selected_job.processing_time:
                # Job is completed, check if it's on time or tardy
                completion_time = t
                if completion_time <= selected_job.deadline:
                    reward_change += selected_job.reward
                else:
                    # Calculate tardiness penalty
                    tardiness = completion_time - selected_job.deadline
                    tardiness_penalty = selected_job.penalty_function.evaluate(tardiness)
                    reward_change += selected_job.reward - tardiness_penalty

    completed_jobs_reward += reward_change

    # final part: compute penalty for unfinished or unscheduled jobs
    for job_instance in jobs.job_instances:
        if list(partial_schedule["content"].values()).count(job_instance.id) < job_instance.processing_time:
            # Job is unfinished, apply penalty
            completed_jobs_reward -= job_instance.drop_penalty

    return completed_jobs_reward


def get_upper_bound_by_MILP(partial_schedule, current_timeslot, jobs):
    '''
    Compute an upper bound for the job assignment using a linear programming relaxation (the original problem is an integer linear programming problem). The computation is done via scipy.optimize.linprog for linear programming.
    '''
    # if penalty functions are all linear
    if all(job_instance.penalty_function.function_type == "linear" for job_instance in jobs.job_instances):

        # The input of linprog are lists, but our job_instance_id are strings. Therefore we need to maintain a mapping between job_instance_id and its index in the lists.
        job_id_to_index = {job_instance.id: index for index, job_instance in enumerate(jobs.job_instances)}
        index_to_job_id = {index: job_instance.id for index, job_instance in enumerate(jobs.job_instances)}
        
        # from now on, we will use job indices instead of job ids for easier handling with linprog.
        # w_i_hat is a list (with the order of job indices) of the reward that is not being subtracted by tardiness penalty for job i, a fixed value
        w_i_hat = [job_instance.reward for job_instance in jobs.job_instances]

        # t_hat is current timestep, a fixed value
        t_hat = current_timeslot - 1 # NOTE: do we need to -1 here?

        # t_i_asterisk is the last time step (so they are integers) by which the penalty of pushing the job back by t_i_asterisk time slots does NOT exceeds the reward of job i
        t_i_asterisk = [0] * num_jobs
        for job_index, job_instance in enumerate(jobs.job_instances):
            slope = job_instance.penalty_function.parameters["slope"]
            intercept = job_instance.penalty_function.parameters["intercept"]
            if slope == 0:
                # penalty is constant, so t_i_asterisk is the final time slot
                t_i_asterisk[job_index] = jobs.total_time_slots
            else:
                t_i_asterisk_value = (w_i_hat[job_index] - intercept) / slope # round down to nearest integer, which make sense because we want the LAST time step that is still WITHIN the reward
                if t_i_asterisk_value < 0:
                    t_i_asterisk[job_index] = 0
                else:
                    t_i_asterisk[job_index] = t_i_asterisk_value

        # r_i is the release time of job i, a fixed value
        r_i = [job_instance.release_time for job_instance in jobs.job_instances]

        # d_i is the deadline of job i, a fixed value
        d_i = [job_instance.deadline for job_instance in jobs.job_instances]

        # p_i is the processing time of job i, a fixed value
        p_i = [job_instance.processing_time for job_instance in jobs.job_instances]

        # f_i is the penalty of pushing a job back (by a number of time slots). Since it is an expression consisting of slope * tardiness + intercept, we define slope and intercept separately.
        f_i_slope = [job_instance.penalty_function.parameters["slope"] for job_instance in jobs.job_instances]
        f_i_intercept = [job_instance.penalty_function.parameters["intercept"] for job_instance in jobs.job_instances]


        # x_i_t denotes whether we schedule job i at time slot t. In the original ILP problem it is a binary **decision** variable, but in the LP relaxation it is a continuous **decision** variable in [0,1].
        # now we construct the coefficients for x_i_t. They are all 0 because they do not appear in the objective function.
        # we will flatten the 2D (job i, time slot t) structure into a 1D list for linprog.
        num_jobs = len(jobs.job_instances)
        num_time_slots = jobs.total_time_slots
        x_i_t_coefficients = [0] * (num_jobs * num_time_slots)

        # now we construct the coefficients for y_i. The coefficient for y_i is w_i_hat.
        y_i_coefficients = [w_i_hat[job_index] for job_index in range(num_jobs)]

        # now we construct the coefficients for t_i_tilde. The coefficient for t_i_tilde is -1 * (f_i_slope).
        t_i_tilde_coefficients = [-f_i_slope[job_index] for job_index in range(num_jobs)]

        # now we construct the coefficients for z_i. The coefficient for z_i is -1 * (f_i_intercept).
        z_i_coefficients = [-f_i_intercept[job_index] for job_index in range(num_jobs)]

        # now we can combine all coefficients to form the final list of coefficients for linprog's objective function. This is done by concatenating the lists in the order of x_i_t, y_i, t_i_tilde, z_i.
        objective_function_coefficients = x_i_t_coefficients + y_i_coefficients + t_i_tilde_coefficients + z_i_coefficients

        # Due to how scipy.optimize.linprog works, the length of objective_function_coefficients is the length of all decision variables. This length will be reused when we construct constraints.
        total_num_decision_variables = len(objective_function_coefficients)

        # now we construct constraints for linprog.
        # For Linprog, constraints are being separated into inequality(<=) constraints, equality(==) constraints, and bounds (constraints of variables themselves).

        # now we construct inequality constraints (A_ub, b_ub).
        # For A_ub, each row corresponds to one inequality constraint, and each column corresponds to one variable (in the order of x_i_t, y_i, t_i_tilde, z_i). So the length of each row is the same as the length of objective_function_coefficients.
        A_ub = [] # a list of lists
        b_ub = [] # a list of real numbers

        # There are a lot of inequality constraints, we will construct them one by one.
        # ub constraint number one: For every time slot from 1 to total_time_slots, sum of x_i_t over i from 1 to total job amount <= 1
        for t in range(num_time_slots):
            constraint_row = [0] * total_num_decision_variables
            for job_index in range(num_jobs):
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
            A_ub.append(constraint_row)
            b_ub.append(1)

        # ub constraint number two: For every job i from 1 to total job amount, z_i <= t_i_tilde
        for job_index in range(num_jobs):
            constraint_row = [0] * total_num_decision_variables
            # coefficient for z_i
            z_i_variable_index = num_jobs * num_time_slots + num_jobs + job_index
            constraint_row[z_i_variable_index] = 1
            # coefficient for t_i_tilde
            t_i_tilde_variable_index = num_jobs * num_time_slots + job_index
            constraint_row[t_i_tilde_variable_index] = -1
            A_ub.append(constraint_row)
            b_ub.append(0)

        # ub constraint number three: For every job i from 1 to total job amount, sum of x_i_t over t from d_i to total_time_slots <= z_i * p_i
        for job_index in range(num_jobs):
            constraint_row = [0] * total_num_decision_variables
            # coefficients for x_i_t
            for t in range(d_i[job_index] - 1, num_time_slots): # t from d_i - 1 to total_time_slots - 1 inclusive, corresponding to time slots from d_i to total_time_slots inclusive.
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
            # coefficient for z_i
            z_i_variable_index = num_jobs * num_time_slots + num_jobs + job_index
            constraint_row[z_i_variable_index] = -p_i[job_index]
            A_ub.append(constraint_row)
            b_ub.append(0)

        # ub constraint number four: For every job i from 1 to total job amount, for every time slot t from d_i to total_time_slots, x_i_t * (t-d_i) <= i_i_tilde, where t in this formula is the time slot index (1-based)
        for job_index in range(num_jobs):
            for t_0_based in range(d_i[job_index] - 1, num_time_slots): # t from d_i - 1 to total_time_slots - 1 inclusive, corresponding to time slots from d_i to total_time_slots inclusive.
                constraint_row = [0] * total_num_decision_variables
                # coefficient for x_i_t
                x_i_t_variable_index = job_index * num_time_slots + t_0_based
                constraint_row[x_i_t_variable_index] = (t_0_based + 1) - d_i[job_index] # (t + 1) because t is 0-based index, but time slots are 1-based.
                # coefficient for t_i_tilde
                t_i_tilde_variable_index = num_jobs * num_time_slots + job_index
                constraint_row[t_i_tilde_variable_index] = -1
                A_ub.append(constraint_row)
                b_ub.append(0)


        # now we construct equality constraints (A_eq, b_eq).
        A_eq = [] # a list of lists
        b_eq = [] # a list of real numbers

        # eq constraint number one: For every job i from 1 to total job amount, sum of x_i_t over t from 1 to total_time_slots == y_i * p_i
        for job_index in range(num_jobs):
            constraint_row = [0] * total_num_decision_variables
            # coefficients for x_i_t
            for t in range(num_time_slots):
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
            # coefficient for y_i
            y_i_variable_index = num_jobs * num_time_slots + job_index
            constraint_row[y_i_variable_index] = -p_i[job_index]
            A_eq.append(constraint_row)
            b_eq.append(0)

        # eq constraint number two: For every job from 1 to total job amount, sum of x_i_t over t from 1 to r_i - 1 == 0
        for job_index in range(num_jobs):
            constraint_row = [0] * total_num_decision_variables
            # coefficients for x_i_t
            for t in range(r_i[job_index] - 1): # t from 0 to r_i - 2 inclusive, corresponding to time slots from 1 to r_i - 1 inclusive.
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
            A_eq.append(constraint_row)
            b_eq.append(0)

        # eq constraint number three: For every job from 1 to total job amount, sum of x_i_t over t from t_i_asterisk to total_time_slots == 0
        for job_index in range(num_jobs):
            constraint_row = [0] * total_num_decision_variables
            # coefficients for x_i_t
            # we need to be careful about the indexing here. t_i_asterisk is in terms of time slots, but our t in the variable indexing is 0-based. so t starts from t_i_asterisk - 1, to total_time_slots - 1 inclusive.
            for t in range(int(t_i_asterisk[job_index]) - 1, num_time_slots): # range is inclusive of start and exclusive of end
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
            A_eq.append(constraint_row)
            b_eq.append(0)

        # now we construct bounds for each variable.
        # For every job i from 1 to total job amount, for every time slot t (1-based obviously) from t_hat to total_time_slots, x_i_t in [0,1]
        bounds = []
        for job_index in range(num_jobs):
            for t_0_based in range(num_time_slots):
                if t_0_based + 1 >= t_hat:
                    bounds.append((0, 1))
                else:
                    # for time slots before current time slot, x_i_t is the value in partial_schedule
                    assigned_job_id = partial_schedule["content"].get(t_0_based + 1, None)
                    if assigned_job_id == index_to_job_id[job_index]:
                        bounds.append((1, 1))
                    else:
                        bounds.append((0, 0))

        # For every job from 1 to total job amount, y_i in [0,1]
        for job_index in range(num_jobs):
            bounds.append((0, 1))

        # For every job from 1 to total job amount, t_i_tilde >= 0
        for job_index in range(num_jobs):
            bounds.append((0, None))

        # For every job from 1 to total job amount, z_i in [0,1]
        for job_index in range(num_jobs):
            bounds.append((0, 1))

    else:
        # not implemented yet
        pass
    

    


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
        for job_instance in jobs.job_instances:
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
            if current_timeslot < jobs.total_time_slots:
                lower_bound_for_this_assumption = get_lower_bound_by_greedy(partial_schedule_assumption, current_timeslot_assumption, jobs)
                upper_bound_for_this_assumption = get_upper_bound_by_MILP(partial_schedule_assumption, current_timeslot_assumption, jobs)
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
            elif current_timeslot == jobs.total_time_slots:  # last time slot, no need to compute bounds for next time slot
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
    jobs = load_jobs_from_input_file("input.json")
    output = schedule_jobs(jobs)
    print("Optimal schedules found:")
    for schedule in output:
        print(schedule)


if __name__ == "__main__":
    main()
