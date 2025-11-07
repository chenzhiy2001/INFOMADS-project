import json
from src.schedule import Schedule
from src.penalty_function import PenaltyFunction
from src.job import Job
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from typing import Optional
from src.schedule import Schedule

def load_jobs_from_input_file(file_path) -> Schedule:
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
        # if not (1 <= job_data["release_time"] < job_data["deadline"] <= (data["total_time_slots"] + 1 )): # deadline itself is not schedulable
            # raise ValueError(f"Job {job_data['id']} has illegal release time {job_data['release_time']} or deadline {job_data['deadline']}. total time slots: {data['total_time_slots']}.")
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

    schedule = Schedule(
        jobs=jobs['job_instances'],
        total_time_slots=max(job.deadline for job in jobs['job_instances'])
    )
    
    return schedule


def display_schedule(schedule: Schedule, figsize=(14, 8), show_plot=True):
    """
    Visualize the schedule using a Gantt chart with matplotlib.
    
    Args:
        schedule: Schedule object containing jobs and their assignments
        figsize: Tuple of (width, height) for the figure size
        show_plot: Whether to display the plot (set to False if you want to save without showing)
    
    Returns:
        fig, ax: The matplotlib figure and axis objects
    """
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, height_ratios=[3, 1])
    
    jobs = schedule.jobs
    T = schedule.T
    schedule_list = schedule.schedule
    
    # Create a color map for jobs
    colors = plt.cm.Set3.colors
    job_colors = {job.id: colors[i % len(colors)] for i, job in enumerate(jobs)}
    
    # ========== Upper plot: Gantt chart ==========
    ax1.set_xlim(0, T + 1)
    ax1.set_ylim(-0.5, len(jobs) + 0.5)
    ax1.set_xlabel('Time Slot', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Job ID', fontsize=12, fontweight='bold')
    ax1.set_title('Schedule Gantt Chart', fontsize=14, fontweight='bold')
    
    # Set y-axis to show job IDs
    job_ids = [job.id for job in jobs]
    ax1.set_yticks(range(len(jobs)))
    ax1.set_yticklabels(job_ids)
    
    # Add grid
    ax1.grid(True, axis='x', alpha=0.3, linestyle='--')
    
    # Plot each job's release time, deadline, and scheduled slots
    for idx, job in enumerate(jobs):
        y_pos = idx
        
        # Draw release time marker (vertical line)
        ax1.axvline(x=job.release_time, ymin=(y_pos - 0.3) / len(jobs), 
                   ymax=(y_pos + 0.3) / len(jobs), color='green', 
                   linewidth=3, alpha=0.7, linestyle='--')
        
        # Draw deadline marker (vertical line)
        ax1.axvline(x=job.deadline, ymin=(y_pos - 0.3) / len(jobs), 
                   ymax=(y_pos + 0.3) / len(jobs), color='red', 
                   linewidth=3, alpha=0.7, linestyle='--')
        
        # Draw shaded region for valid time window (release to deadline)
        rect = mpatches.Rectangle((job.release_time, y_pos - 0.4), 
                                   job.deadline - job.release_time, 0.8,
                                   linewidth=0, edgecolor='none', 
                                   facecolor='lightgray', alpha=0.2)
        ax1.add_patch(rect)
    
    # Draw scheduled slots
    for t, job_id in enumerate(schedule_list):
        if job_id is not None:
            # Find the job index
            job_idx = next((i for i, job in enumerate(jobs) if job.id == job_id), None)
            if job_idx is not None:
                job = jobs[job_idx]
                # Check if this slot is before or after deadline
                is_late = t >= job.deadline
                
                # Draw the scheduled slot
                rect = mpatches.Rectangle((t, job_idx - 0.35), 1, 0.7,
                                          linewidth=2, 
                                          edgecolor='black' if not is_late else 'darkred',
                                          facecolor=job_colors[job_id],
                                          alpha=0.8 if not is_late else 0.9,
                                          hatch='//' if is_late else None)
                ax1.add_patch(rect)
                
                # Add time slot label inside the rectangle
                ax1.text(t + 0.5, job_idx, str(t), 
                        ha='center', va='center', fontsize=8, fontweight='bold')
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor='white', edgecolor='green', linestyle='--', 
                      linewidth=2, label='Release Time'),
        mpatches.Patch(facecolor='white', edgecolor='red', linestyle='--', 
                      linewidth=2, label='Deadline'),
        mpatches.Patch(facecolor='lightblue', edgecolor='black', 
                      linewidth=2, label='On-time Execution'),
        mpatches.Patch(facecolor='lightcoral', edgecolor='darkred', 
                      linewidth=2, hatch='//', label='Late Execution')
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # ========== Lower plot: Job details table ==========
    ax2.axis('off')
    
    # Prepare table data
    table_data = []
    table_data.append(['Job ID', 'Release', 'Deadline', 'Proc. Time', 
                      'Reward', 'Drop Pen.', 'Status', 'Completion'])
    
    for job in jobs:
        # Calculate completion time
        completion_time = None
        if job.completed or any(job_id == job.id for job_id in schedule_list):
            scheduled_slots = [t for t, job_id in enumerate(schedule_list) if job_id == job.id]
            if scheduled_slots:
                completion_time = max(scheduled_slots) + 1  # +1 because slots are 0-indexed
        
        status = 'Completed' if job.completed else 'Incomplete'
        completion_str = str(completion_time) if completion_time else 'N/A'
        
        # Check if late
        if completion_time and completion_time > job.deadline:
            status = f'Late (t={completion_time - job.deadline})'
        
        table_data.append([
            job.id,
            str(job.release_time),
            str(job.deadline),
            str(job.processing_time),
            f'{job.reward:.1f}',
            f'{job.drop_penalty:.1f}',
            status,
            completion_str
        ])
    
    # Create table
    table = ax2.table(cellText=table_data, cellLoc='center', loc='center',
                     colWidths=[0.12, 0.10, 0.10, 0.12, 0.10, 0.11, 0.18, 0.12])
    
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    
    # Style the header row
    for i in range(len(table_data[0])):
        cell = table[(0, i)]
        cell.set_facecolor('#4CAF50')
        cell.set_text_props(weight='bold', color='white')
    
    # Color code status cells
    for i in range(1, len(table_data)):
        status_cell = table[(i, 6)]
        if 'Completed' in table_data[i][6] and 'Late' not in table_data[i][6]:
            status_cell.set_facecolor('#C8E6C9')
        elif 'Late' in table_data[i][6]:
            status_cell.set_facecolor('#FFCDD2')
        else:
            status_cell.set_facecolor('#FFE0B2')
    
    # Add score to the figure
    score = schedule.score()
    fig.suptitle(f'Schedule Visualization (Score: {score:.2f})', 
                fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout()
    
    if show_plot:
        plt.show()
    
    return fig, (ax1, ax2)