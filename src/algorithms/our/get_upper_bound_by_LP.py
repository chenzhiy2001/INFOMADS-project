# scipy for MILP
from math import floor
from scipy.optimize import linprog

from src.schedule import Schedule
from src.job import Job

import numpy as np

def LP_linear(schedule: Schedule) -> float:
    w_i_hat = [job_instance.reward + job_instance.drop_penalty for job_instance in schedule.jobs]

    num_jobs = len(schedule.jobs)

    # r_i is the release time of job i, a fixed value
    r_i = [job_instance.release_time for job_instance in schedule.jobs]
    t_i_asterisk = [job_instance.t_i_asterisk for job_instance in schedule.jobs]
    # d_i is the deadline of job i, a fixed value
    d_i = [job_instance.deadline for job_instance in schedule.jobs]

    # p_i is the processing time of job i, a fixed value
    p_i = [job_instance.processing_time for job_instance in schedule.jobs]

    # f_i is the penalty of pushing a job back (by a number of time slots). 
    # Since it is an expression consisting of slope * tardiness + intercept, we define slope and intercept separately.
    f_i_slope = [job_instance.penalty_function.parameters["slope"] for job_instance in schedule.jobs]
    f_i_intercept = [job_instance.penalty_function.parameters["intercept"] for job_instance in schedule.jobs]


    # x_i_t denotes whether we schedule job i at time slot t. In the original ILP problem it is a binary **decision** variable, but in the LP relaxation it is a continuous **decision** variable in [0,1].
    # now we construct the coefficients for x_i_t. They are all 0 because they do not appear in the objective function.
    # we will flatten the 2D (job i, time slot t) structure into a 1D list for linprog.
    num_time_slots = schedule.T
    
    x_i_t_coefficients = [0] * (num_jobs * num_time_slots)

    # now we construct the coefficients for y_i. The coefficient for y_i is w_i_hat.
    # y_i_coefficients = [w_i_hat[job_index] for job_index in range(num_jobs)]
    y_i_coefficients = w_i_hat

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
            # variable_index = job_index + num_time_slots * t
            # print(variable_index, len(constraint_row))
            constraint_row[variable_index] = 1
        A_ub.append(constraint_row)
        b_ub.append(1)

    # ub constraint number two: For every job i from 1 to total job amount, z_i <= t_i_tilde
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        # coefficient for z_i
        z_i_variable_index = num_jobs * num_time_slots + num_jobs + num_jobs + job_index
        constraint_row[z_i_variable_index] = 1
        # coefficient for t_i_tilde
        t_i_tilde_variable_index = num_jobs * num_time_slots + num_jobs + job_index
        constraint_row[t_i_tilde_variable_index] = -1
        A_ub.append(constraint_row)
        b_ub.append(0)

    # ub constraint number three: For every job i from 1 to total job amount, sum of x_i_t over t from d_i to total_time_slots <= z_i * p_i
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        # coefficients for x_i_t
        # todo: check if we need to add a -1 here
        for t in range(d_i[job_index], num_time_slots): # t from d_i - 1 to total_time_slots - 1 inclusive, corresponding to time slots from d_i to total_time_slots inclusive.
            variable_index = job_index * num_time_slots + t
            constraint_row[variable_index] = 1
        # coefficient for z_i
        z_i_variable_index = num_jobs * num_time_slots + num_jobs + num_jobs + job_index
        constraint_row[z_i_variable_index] = -p_i[job_index]
        A_ub.append(constraint_row)
        b_ub.append(0)

    # ub constraint number four: For every job i from 1 to total job amount, for every time slot t from d_i to total_time_slots, x_i_t * (t-d_i) <= i_i_tilde, where t in this formula is the time slot index (1-based)
    for job_index in range(num_jobs):
        # todo: same as above
        for t_0_based in range(d_i[job_index], num_time_slots): # t from d_i - 1 to total_time_slots - 1 inclusive, corresponding to time slots from d_i to total_time_slots inclusive.
            constraint_row = [0] * total_num_decision_variables
            # coefficient for x_i_t
            x_i_t_variable_index = job_index * num_time_slots + t_0_based
            # do we add a +1 here?
            constraint_row[x_i_t_variable_index] = (t_0_based) - d_i[job_index] # (t + 1) because t is 0-based index, but time slots are 1-based.
            # coefficient for t_i_tilde
            t_i_tilde_variable_index = num_jobs * num_time_slots + num_jobs + job_index
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
        if r_i[job_index] > 0:
            for t in range(r_i[job_index]): # t from 0 to r_i - 2 inclusive, corresponding to time slots from 1 to r_i - 1 inclusive.
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
        A_eq.append(constraint_row)
        b_eq.append(0)

    # eq constraint number three: For every job from 1 to total job amount, sum of x_i_t over t from t_i_asterisk to total_time_slots == 0
    # Note: t_i_asterisk represents maximum acceptable tardiness (not an absolute time slot)
    # The constraint means: cannot schedule job at time slots >= (deadline + t_i_asterisk)
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        # coefficients for x_i_t
        # Maximum completion time is deadline + t_i_asterisk
        # We cannot schedule at time slots >= max_completion_time
        max_completion_time = d_i[job_index] + int(t_i_asterisk[job_index])
        if max_completion_time < num_time_slots:
            for t in range(max_completion_time, num_time_slots):
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
        A_eq.append(constraint_row)
        b_eq.append(0)

    # now we construct bounds for each variable.
    # For every job i from 1 to total job amount, for every time slot t (1-based obviously) from t_hat to total_time_slots, x_i_t in [0,1]
    bounds = []
    for job_index in range(num_jobs):
        for t_0_based in range(num_time_slots):
            # bounds.append((0, 1))

            if t_0_based <= schedule.t:
                if schedule.schedule[t_0_based] is not None:
                    scheduled_job = schedule.schedule[t_0_based]
                    index_of_scheduled_job = schedule.jobs.index(schedule.get_job_from_id(scheduled_job))

                    if index_of_scheduled_job == job_index:
                        bounds.append((1, 1))
                    else:
                        bounds.append((0, 0))
                else:
                    bounds.append((0, 0))
            else:
                bounds.append((0, 1))

            # if t_0_based + 1 >= t_hat:
            #     bounds.append((0, 1))
            # else:
            #     # for time slots before current time slot, x_i_t is the value in partial_schedule
            #     assigned_job_id = partial_schedule["content"].get(t_0_based + 1, None)
            #     if assigned_job_id == index_to_job_id[job_index]:
            #         bounds.append((1, 1))
            #     else:
                    # bounds.append((0, 0))

    # For every job from 1 to total job amount, y_i in [0,1]
    for job_index in range(num_jobs):
        bounds.append((0, 1))

    # For every job from 1 to total job amount, t_i_tilde >= 0
    for job_index in range(num_jobs):
        bounds.append((0, None))

    # For every job from 1 to total job amount, z_i in [0,1]
    for job_index in range(num_jobs):
        bounds.append((0, 1))
    # I thought linprog is maximizing by default, but it turns out it is minimizing by default. Therefore we need to negate the objective function coefficients to convert our maximization problem into a minimization problem.
    objective_function_coefficients = [-coeff for coeff in objective_function_coefficients]

    res = linprog(c=objective_function_coefficients, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    # res = linprog(c=objective_function_coefficients, A_ub=A_ub, b_ub=b_ub, A_eq=None, b_eq=None, bounds=bounds, method='highs')
    
    # Check if the optimization was successful
    if not res.success:
        print(f"Linear program failed: {res.message}")
        print(f"Status: {res.status}")
        print(f"Number of jobs: {num_jobs}, Number of time slots: {num_time_slots}")
        print(f"Number of decision variables: {total_num_decision_variables}")
        print(f"Number of inequality constraints: {len(A_ub)}")
        print(f"Number of equality constraints: {len(A_eq)}")
        raise ValueError(f"Linear program optimization failed: {res.message}")
    
    return -res.fun  # negate back to get the maximized value


def LP_per_timeslot(schedule: Schedule) -> float:
    """
    LP formulation based on per-timeslot penalty function.
    
    Variables:
    - x_{i,t}: binary variable indicating if job i is scheduled at time t
    - y_i: binary variable indicating if job i is accepted
    - tilde{t_i^{(j)}}: binary variable indicating if job i has tardiness level j
    
    Objective:
    max sum_i w_hat_i * y_i - sum_i sum_j tilde{t_i^{(j)}} * a_i^{(j)}
    
    where a_i^{(j)} is the penalty for job i at tardiness level j
    """
    w_i_hat = [job_instance.reward + job_instance.drop_penalty for job_instance in schedule.jobs]

    num_jobs = len(schedule.jobs)

    # r_i is the release time of job i, a fixed value
    r_i = [job_instance.release_time for job_instance in schedule.jobs]
    t_i_asterisk = [job_instance.t_i_asterisk for job_instance in schedule.jobs]
    # d_i is the deadline of job i, a fixed value
    d_i = [job_instance.deadline for job_instance in schedule.jobs]

    # p_i is the processing time of job i, a fixed value
    p_i = [job_instance.processing_time for job_instance in schedule.jobs]

    num_time_slots = schedule.T
    
    # Calculate penalty values a_i^{(j)} for each job i and each tardiness level j
    # a_i^{(j)} is the penalty when job i is tardy by j time slots
    a_i_j = []
    for job_instance in schedule.jobs:
        penalties_for_job = []
        for j in range(int(job_instance.t_i_asterisk) + 1):
            # Penalty at tardiness level j
            penalty = job_instance.penalty_function.calculate(j)
            penalties_for_job.append(penalty)
        a_i_j.append(penalties_for_job)
    
    # Decision variables structure:
    # 1. x_{i,t} for all jobs i and time slots t: num_jobs * num_time_slots variables
    # 2. y_i for all jobs i: num_jobs variables
    # 3. tilde{t_i^{(j)}} for all jobs i and tardiness levels j (0 to t_i_asterisk): sum_i (t_i_asterisk_i + 1) variables
    
    # Construct objective function coefficients
    # x_{i,t} coefficients: all 0 (don't appear in objective)
    x_i_t_coefficients = [0] * (num_jobs * num_time_slots)
    
    # y_i coefficients: w_i_hat
    y_i_coefficients = w_i_hat.copy()
    
    # tilde{t_i^{(j)}} coefficients: -a_i^{(j)}
    tilde_t_i_j_coefficients = []
    for job_index in range(num_jobs):
        for j in range(len(a_i_j[job_index])):
            tilde_t_i_j_coefficients.append(-a_i_j[job_index][j])
    
    # Combine all coefficients
    objective_function_coefficients = x_i_t_coefficients + y_i_coefficients + tilde_t_i_j_coefficients
    
    total_num_decision_variables = len(objective_function_coefficients)
    
    # Helper function to get variable index for tilde{t_i^{(j)}}
    def get_tilde_t_index(job_idx, tardiness_level):
        base_index = num_jobs * num_time_slots + num_jobs
        offset = sum(len(a_i_j[i]) for i in range(job_idx))
        return base_index + offset + tardiness_level
    
    # Construct constraints
    A_ub = []  # inequality constraints (<=)
    b_ub = []
    A_eq = []  # equality constraints (==)
    b_eq = []
    
    # Constraint 1: sum_i x_{i,t} <= 1 for all t (resource capacity)
    for t in range(num_time_slots):
        constraint_row = [0] * total_num_decision_variables
        for job_index in range(num_jobs):
            variable_index = job_index * num_time_slots + t
            constraint_row[variable_index] = 1
        A_ub.append(constraint_row)
        b_ub.append(1)
    
    # Constraint 2: sum_{t'=0}^{t_i^*} tilde{t_i^{(t')}} <= 1 for all i
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        for j in range(len(a_i_j[job_index])):
            tilde_t_idx = get_tilde_t_index(job_index, j)
            constraint_row[tilde_t_idx] = 1
        A_ub.append(constraint_row)
        b_ub.append(1)
    
    # Constraint 3: x_{i,t} * (t - d_i) <= sum_{t'=1}^T (t' - d_i) * tilde{t_i^{(t')}}
    # This is: x_{i,t} * (t - d_i) - sum_{t'=1}^T (t' - d_i) * tilde{t_i^{(t')}} <= 0
    # for all i, for all t >= d_i
    for job_index in range(num_jobs):
        deadline = d_i[job_index]
        for t_0_based in range(deadline, num_time_slots):
            constraint_row = [0] * total_num_decision_variables
            
            # Coefficient for x_{i,t}
            x_i_t_variable_index = job_index * num_time_slots + t_0_based
            # t_0_based is 0-indexed, but represents time slot t_0_based+1 in 1-indexed
            # Actually, looking at the code, it seems t_0_based is used directly as the time value
            constraint_row[x_i_t_variable_index] = t_0_based - deadline
            
            # Coefficients for tilde{t_i^{(t')}}
            # Note: tardiness level j corresponds to being tardy by j time slots
            # So if job completes at time (deadline + j), tardiness is j
            for j in range(len(a_i_j[job_index])):
                tilde_t_idx = get_tilde_t_index(job_index, j)
                # t' - d_i = j (tardiness level)
                constraint_row[tilde_t_idx] = -j
            
            A_ub.append(constraint_row)
            b_ub.append(0)
    
    # Equality Constraint 1: sum_t x_{i,t} = y_i * p_i for all i
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        # Coefficients for x_{i,t}
        for t in range(num_time_slots):
            variable_index = job_index * num_time_slots + t
            constraint_row[variable_index] = 1
        # Coefficient for y_i
        y_i_variable_index = num_jobs * num_time_slots + job_index
        constraint_row[y_i_variable_index] = -p_i[job_index]
        A_eq.append(constraint_row)
        b_eq.append(0)
    
    # Equality Constraint 2: sum_{t=1}^{r_i-1} x_{i,t} = 0 for all i (release time)
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        if r_i[job_index] > 0:
            for t in range(r_i[job_index]):
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
        A_eq.append(constraint_row)
        b_eq.append(0)
    
    # Equality Constraint 3: sum_{t=t_i^*}^T x_{i,t} = 0 for all i (maximum tardiness)
    # Note: t_i^* means deadline + t_i_asterisk
    for job_index in range(num_jobs):
        constraint_row = [0] * total_num_decision_variables
        max_completion_time = d_i[job_index] + int(t_i_asterisk[job_index])
        if max_completion_time < num_time_slots:
            for t in range(max_completion_time, num_time_slots):
                variable_index = job_index * num_time_slots + t
                constraint_row[variable_index] = 1
        A_eq.append(constraint_row)
        b_eq.append(0)
    
    # Bounds for variables
    bounds = []
    
    # Bounds for x_{i,t}: [0,1] or fixed based on current schedule
    for job_index in range(num_jobs):
        for t_0_based in range(num_time_slots):
            if t_0_based <= schedule.t:
                if schedule.schedule[t_0_based] is not None:
                    scheduled_job = schedule.schedule[t_0_based]
                    index_of_scheduled_job = schedule.jobs.index(schedule.get_job_from_id(scheduled_job))
                    if index_of_scheduled_job == job_index:
                        bounds.append((1, 1))
                    else:
                        bounds.append((0, 0))
                else:
                    bounds.append((0, 0))
            else:
                bounds.append((0, 1))
    
    # Bounds for y_i: [0,1]
    for job_index in range(num_jobs):
        bounds.append((0, 1))
    
    # Bounds for tilde{t_i^{(j)}}: [0,1]
    for job_index in range(num_jobs):
        for j in range(len(a_i_j[job_index])):
            bounds.append((0, 1))
    
    # Negate objective coefficients for minimization
    objective_function_coefficients = [-coeff for coeff in objective_function_coefficients]
    
    res = linprog(c=objective_function_coefficients, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')
    
    # Check if the optimization was successful
    if not res.success:
        print(f"Linear program failed: {res.message}")
        print(f"Status: {res.status}")
        print(f"Number of jobs: {num_jobs}, Number of time slots: {num_time_slots}")
        print(f"Number of decision variables: {total_num_decision_variables}")
        print(f"Number of inequality constraints: {len(A_ub)}")
        print(f"Number of equality constraints: {len(A_eq)}")
        raise ValueError(f"Linear program optimization failed: {res.message}")
    
    return -res.fun  # negate back to get the maximized value


def get_upper_bound_by_LP(schedule: Schedule) -> float:
    '''
    Compute an upper bound for the job assignment using a linear programming relaxation (the original problem is an integer linear programming problem). 
    The computation is done via scipy.optimize.linprog for linear programming.
    '''
    # if penalty functions are all linear
    if all(job.penalty_function.function_type == "linear" for job in schedule.jobs):
        return LP_linear(schedule)

    # if penalty functions are all per-timeslot
    return LP_per_timeslot(schedule)
    
