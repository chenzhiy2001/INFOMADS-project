# Procrastinating is Not Always Bad

Github Repository: <https://github.com/chenzhiy2001/INFOMADS-project>


> ⚠️ \
> In our project, jobs can be scheduled on the release time but can **not** be scheduled on the deadline



## Setup
**Using `uv`.** To run our program, we recommend to have uv installed (https://docs.astral.sh/uv/), as then you automatically have the same packages and python version.

**Using "traditional" python**. We provide a `requirements.txt` file, which ensures that we have the same packages installed. Note that we developped our code using Python 3.9.

## Run

Execute our program using
```
uv run main.py <input> <algorithm> <setting> <output_path>
```

**input**
- The path to the input file. We support two formats: txt and json.
    - If a txt file is provided (as described in the project description), we set the push-back functions to sub-optimal results, therefore pushing a job back will never be optimal in this case.
    - If a json is provided (template as in `input.json`), we allow the user to provide a specific push-back cost function.

**algorithm**
- Right now, we only support our own algorithm, so only `ours` is supported

**setting**
- To specify whether the scheduler should process the file in a `online` or `offline` setting. 

**output_path**
- Optional
- If specified, we return the schedule as txt file as specified in the project description.
- If not specified, we only display the plot using matplotlib.

### Example
We can run an instance of our offline scheduler as 
```bash
uv run main.py tests/Job-7.txt ours offline 
```

> ⚠️ \
> When running the project, you'll see that every timeslot is being displayed one timeslot earlier. This is because timeslot t=0 is our first time slot internally. However, this does not affect the relative schedule; simply add +1 to the timeslots and you have the correct schedule.

### Job Definition

While you can define the exact push-back function using the `.json` file format, if not provided, we assume that the user does not want to allow job-pushback, and we set the push-back cost of each job as $f_i(t) = \alpha \cdot t + \beta$ with 
- $\alpha = 2 \cdot (w_i + \ell_i)$
- $\beta = 2 \cdot (w_i + \ell_i)$ 

This garantees that the cost of pushing a job back, even by just one time slot, is already greater than the reward it can get.

## Runtime ⚠️

### Offline
Because our Integer Linear Program has many variables, we observe that the LP relaxation drastically over-estimates the upper-bound of each branch in the branch and bound algorithm. This decreases the number of branches we are able to cut.

<!-- Therefore our runtime is **close to bruteforce** as we essentially cut almost no branches. Keep this in mind when running our offline algorithm. -->

Furthermore, as python is not the fastest programming language, the runtime could be improved by implementing our algorithm in a compiled language (like Rust).

### Online
This algorithm is very fast. But not very good :/