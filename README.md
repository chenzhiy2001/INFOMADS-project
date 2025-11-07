# Procrastinating is Not Always Bad

Github Repository: <https://github.com/chenzhiy2001/INFOMADS-project>

## Setup
**You have `uv`.** To run our program, we recommend to have uv installed (https://docs.astral.sh/uv/), as then you automatically have the same packages and python version.

**You prefer to use another tool**. We provide a `requirements.txt` file, which ensures that we have the same packages installed. Note that we developped our code using Python 3.9.

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