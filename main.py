#!/usr/bin/env python3
import argparse
import os
import json
from datetime import datetime, timedelta
from visualize import create_visualizations

# ---------------- Constants & Configurations ---------------- #

# The starting time for your day – change this if needed.
START_TIME_STR = "07:00"  # Format: HH:MM

# Length of each interval in minutes.
INTERVAL_MINUTES = 15

# Total intervals per 24 hours (24 * 60 / 15)
INTERVALS_PER_DAY = 96

# Directory where schedule records are stored.
RECORDS_DIR = "records"


# ---------------- Helper Functions ---------------- #

def ensure_records_dir():
    """Ensure that the directory for storing records exists."""
    os.makedirs(RECORDS_DIR, exist_ok=True)


def get_day_start_datetime(day: datetime, start_time_str=START_TIME_STR):
    """Return a datetime corresponding to the given day with the start time."""
    hour, minute = map(int, start_time_str.split(":"))
    return datetime(day.year, day.month, day.day, hour, minute)


def get_intervals_for_day(day_start: datetime):
    """Return a list of (start, end) tuples for each 15-minute interval starting at day_start."""
    intervals = []
    for i in range(INTERVALS_PER_DAY):
        start = day_start + timedelta(minutes=i * INTERVAL_MINUTES)
        end = start + timedelta(minutes=INTERVAL_MINUTES)
        intervals.append((start, end))
    return intervals


def load_schedule(date_str):
    """Load the schedule for a given date (YYYY-MM-DD) from file."""
    file_path = os.path.join(RECORDS_DIR, f"{date_str}.json")
    if not os.path.exists(file_path):
        return None
    with open(file_path, "r") as f:
        return json.load(f)


def save_schedule(date_str, data):
    """Save the schedule data to the file corresponding to the date."""
    file_path = os.path.join(RECORDS_DIR, f"{date_str}.json")
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Schedule saved to {file_path}")


def parse_task_input(task_str: str):
    """
    Parse the input string into a hierarchical list.
    For example, "work: code: project A" becomes ['work', 'code', 'project A'].
    """
    return [s.strip() for s in task_str.split(":") if s.strip()]


# ---------------- Recording & Updating ---------------- #

def record_day(schedule_date: datetime):
    """
    Interactively record a schedule for the day.
    If a schedule file already exists for the day and is incomplete,
    resume from where you left off.
    
    Entering "sleep" auto-fills the rest of the day as sleep.
    Entering "exit" saves progress and exits.
    """
    ensure_records_dir()
    date_str = schedule_date.strftime("%Y-%m-%d")
    existing_data = load_schedule(date_str)
    if existing_data:
        schedule = existing_data.get("schedule", [])
        current_index = len(schedule)
        print(f"Resuming schedule for {date_str} from interval {current_index+1}...")
    else:
        schedule = []
        current_index = 0

    day_start = get_day_start_datetime(schedule_date)
    intervals = get_intervals_for_day(day_start)
    total_intervals = len(intervals)

    for idx in range(current_index, total_intervals):
        start, end = intervals[idx]
        time_slot = f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}"
        task_input = input(f"{time_slot}: ").strip()
        if task_input.lower() == "sleep":
            # Record current interval as sleep and fill remainder with sleep.
            schedule.append({"time_slot": time_slot, "task": ["sleep"]})
            for j in range(idx+1, total_intervals):
                s, e = intervals[j]
                slot = f"{s.strftime('%H:%M')}-{e.strftime('%H:%M')}"
                schedule.append({"time_slot": slot, "task": ["sleep"]})
            break
        elif task_input.lower() == "exit":
            print("Exiting. Progress saved.")
            break
        else:
            tasks = parse_task_input(task_input)
            schedule.append({"time_slot": time_slot, "task": tasks})

    data = {"date": date_str, "start_time": START_TIME_STR, "schedule": schedule}
    save_schedule(date_str, data)


def update_day(update_date_str):
    """
    Re-run the record program for a specific day.
    For each interval, display the previous hierarchical task (as colon-separated text)
    and allow you to press ENTER to keep it or enter a new value.
    """
    data = load_schedule(update_date_str)
    if not data:
        print("No schedule recorded for that date. Use record mode to create one.")
        return

    schedule = data.get("schedule", [])
    print(f"\n--- Updating schedule for {update_date_str} ---")
    for idx, item in enumerate(schedule):
        # Show previous tasks as a colon-separated string.
        prev_tasks = item["task"] if isinstance(item["task"], list) else [item["task"]]
        prev_str = ": ".join(prev_tasks)
        prompt = f"{item['time_slot']} (previous: {prev_str}): "
        new_input = input(prompt).strip()
        if new_input:
            schedule[idx]["task"] = parse_task_input(new_input)
    data["schedule"] = schedule
    save_schedule(update_date_str, data)


def show_day():
    """Ask for a date and display the schedule for that day with hierarchical tasks."""
    date_input = input("Enter date (YYYY-MM-DD): ").strip()
    data = load_schedule(date_input)
    if not data:
        print("No schedule recorded for that date.")
        return
    print(f"\n--- Schedule for {date_input} ---")
    for item in data.get("schedule", []):
        tasks = item["task"] if isinstance(item["task"], list) else [item["task"]]
        print(f"{item['time_slot']}: {': '.join(tasks)}")
    print("-" * 40)


# ---------------- Analysis ---------------- #

def update_tree(tree, tasks):
    """
    Recursively update the tree with the hierarchical task list.
    Each node in the tree is a dict of the form:
      { "task_name": {"count": int, "children": { ... } } }
    """
    if not tasks:
        return
    task = tasks[0].strip().lower()
    if task not in tree:
        tree[task] = {"count": 0, "children": {}}
    tree[task]["count"] += 1
    update_tree(tree[task]["children"], tasks[1:])


def print_tree(tree, parent_count, indent=""):
    """Recursively print the aggregated tree with percentages."""
    for task, data in tree.items():
        perc = (data["count"] / parent_count) * 100 if parent_count > 0 else 0
        print(f"{indent}{task}: {perc:.2f}% ({data['count']} intervals)")
        if data["children"]:
            print_tree(data["children"], data["count"], indent + "    - ")


def analyze_period(period):
    """
    Analyze schedules over a period (week/month) and print the percentage of time spent
    on different tasks and sub-tasks.
    """
    period = period.lower()
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    else:
        print("Unknown period. Use 'week' or 'month'.")
        return

    today = datetime.today()
    start_date = today - timedelta(days=days - 1)
    total_intervals = 0
    task_tree = {}

    ensure_records_dir()
    for filename in os.listdir(RECORDS_DIR):
        if filename.endswith(".json"):
            try:
                file_date = datetime.strptime(filename[:-5], "%Y-%m-%d")
            except ValueError:
                continue
            if start_date.date() <= file_date.date() <= today.date():
                file_path = os.path.join(RECORDS_DIR, filename)
                with open(file_path, "r") as f:
                    data = json.load(f)
                schedule = data.get("schedule", [])
                for item in schedule:
                    total_intervals += 1
                    tasks = item["task"]
                    if not isinstance(tasks, list):
                        tasks = [tasks]
                    update_tree(task_tree, tasks)

    if total_intervals == 0:
        print("No schedule data found for the specified period.")
        return

    print(f"\n--- Analysis for the last {days} days ---")
    print_tree(task_tree, total_intervals, indent="")
    print("-" * 40)
    
    # Create visualizations
    create_visualizations(task_tree, total_intervals)


# ---------------- Main CLI ---------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Time Tracker: Record, view, update, and analyze your day in 15-minute intervals with hierarchical tasks."
    )
    parser.add_argument("--show", action="store_true", help="Show schedule for a day")
    parser.add_argument("--analyze", type=str, metavar="PERIOD", help="Analyze schedule for a period ('week' or 'month')")
    parser.add_argument("--update", type=str, metavar="YYYY-MM-DD", help="Update schedule for a given date (YYYY-MM-DD)")
    args = parser.parse_args()

    if args.show:
        show_day()
    elif args.analyze:
        analyze_period(args.analyze)
    elif args.update:
        update_day(args.update)
    else:
        # Determine which day to record for.
        now = datetime.now()
        day_start = get_day_start_datetime(now)
        if now < day_start:
            schedule_date = now - timedelta(days=1)
        else:
            schedule_date = now
        record_day(schedule_date)


if __name__ == "__main__":
    main()
