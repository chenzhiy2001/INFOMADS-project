# scipy for MILP
from math import floor
from scipy.optimize import linprog

def get_upper_bound_by_LP(partial_schedule, current_timeslot, jobs):
    '''
    Compute an upper bound for the job assignment using a linear programming relaxation (the original problem is an integer linear programming problem). The computation is done via scipy.optimize.linprog for linear programming.
    '''
    # if penalty functions are all linear
    if all(job_instance.penalty_function.function_type == "linear" for job_instance in jobs["job_instances"]):

        # The input of linprog are lists, but our job_instance_id are strings. Therefore we need to maintain a mapping between job_instance_id and its index in the lists.
        job_id_to_index = {job_instance.id: index for index, job_instance in enumerate(jobs["job_instances"])}
        index_to_job_id = {index: job_instance.id for index, job_instance in enumerate(jobs["job_instances"])}
        
        # from now on, we will use job indices instead of job ids for easier handling with linprog.
        # w_i_hat is a list (with the order of job indices) of the reward that is not being subtracted by tardiness penalty for job i, a fixed value
        w_i_hat = [job_instance.reward for job_instance in jobs["job_instances"]]

        # t_hat is current timestep, a fixed value
        t_hat = current_timeslot - 1 # NOTE: do we need to -1 here?

        # t_i_asterisk is the last time step (so they are integers) by which the penalty of pushing the job back by t_i_asterisk time slots does NOT exceeds the reward of job i
        t_i_asterisk = [0] * num_jobs
        for job_index, job_instance in enumerate(jobs["job_instances"]):
            slope = job_instance.penalty_function.parameters["slope"]
            intercept = job_instance.penalty_function.parameters["intercept"]
            if slope == 0:
                # penalty is constant, so t_i_asterisk is the final time slot
                t_i_asterisk[job_index] = jobs.total_time_slots
            else:
                t_i_asterisk_value = floor((w_i_hat[job_index] - intercept) / slope) # round down to nearest integer, which make sense because we want the LAST time step that is still WITHIN the reward
                if t_i_asterisk_value < 0:
                    t_i_asterisk[job_index] = 0
                else:
                    t_i_asterisk[job_index] = t_i_asterisk_value

        # r_i is the release time of job i, a fixed value
        r_i = [job_instance.release_time for job_instance in jobs["job_instances"]]

        # d_i is the deadline of job i, a fixed value
        d_i = [job_instance.deadline for job_instance in jobs["job_instances"]]

        # p_i is the processing time of job i, a fixed value
        p_i = [job_instance.processing_time for job_instance in jobs["job_instances"]]

        # f_i is the penalty of pushing a job back (by a number of time slots). Since it is an expression consisting of slope * tardiness + intercept, we define slope and intercept separately.
        f_i_slope = [job_instance.penalty_function.parameters["slope"] for job_instance in jobs["job_instances"]]
        f_i_intercept = [job_instance.penalty_function.parameters["intercept"] for job_instance in jobs["job_instances"]]


        # x_i_t denotes whether we schedule job i at time slot t. In the original ILP problem it is a binary **decision** variable, but in the LP relaxation it is a continuous **decision** variable in [0,1].
        # now we construct the coefficients for x_i_t. They are all 0 because they do not appear in the objective function.
        # we will flatten the 2D (job i, time slot t) structure into a 1D list for linprog.
        num_jobs = len(jobs["job_instances"])
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
    
