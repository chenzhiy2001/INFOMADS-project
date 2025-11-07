

class PenaltyFunction:
    '''A penalty function is defined by:
    - a string of function type: "per-timeslot", "linear"
    - an object defining the function parameters:
      - "per-timeslot": a list of (time, penalty) points, can be used to define step-wise functions
      - "linear": a slope (real number) and an intercept (real number)
    '''
    def __init__(self, function_type: str, parameters: dict):
        self.function_type = function_type
        if function_type not in ["per-timeslot", "linear"]:
            raise ValueError("Invalid function type. Must be 'per-timeslot' or 'linear'.")
        elif function_type == "per-timeslot":
            # Each point must be a tuple of (time (int), penalty (real)), time must be positive and penalty values must be non-negative.
            if not isinstance(parameters, list) or not all(
                isinstance(point, list) and len(point) == 2 and
                isinstance(point[0], int) and point[0] > 0 and
                isinstance(point[1], (int, float)) and point[1] >= 0
                for point in parameters):
                raise ValueError("Parameters for 'per-timeslot' must be a list of (time (int > 0), penalty (real >= 0)) points.")
            # Ensure non-decreasing non-negative function. 
            if any(
                parameters[i][1] > parameters[i+1][1] for i in range(len(parameters)-1)):
                raise ValueError("Penalty values must be non-decreasing.")
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
    
    def evaluate(self, tardiness):
        '''Evaluate the penalty function at a given tardiness value (integer, > 0)'''
        if tardiness <= 0:
            raise ValueError("Tardiness must be positive.")
        if self.function_type == "per-timeslot":
            tardiness_penalty_points = self.parameters
            tardiness_penalty = 0
            for point in tardiness_penalty_points:
                if tardiness >= point[0]:
                    tardiness_penalty = point[1]
                else:
                    break
            return tardiness_penalty
        elif self.function_type == "linear":
            slope = self.parameters["slope"]
            intercept = self.parameters["intercept"]
            return slope * tardiness + intercept