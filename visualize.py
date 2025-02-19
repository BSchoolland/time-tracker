#!/usr/bin/env python3
import matplotlib.pyplot as plt
import numpy as np

def flatten_tree(tree, parent="", result=None):
    """Convert the nested tree structure into flat dictionaries for visualization."""
    if result is None:
        result = {"main": {}, "sub": {}}
    
    for task, data in tree.items():
        # Add to main tasks
        if not parent:
            result["main"][task] = data["count"]
        else:
            # Add to sub tasks under their parent
            parent_key = f"{parent}"
            if parent_key not in result["sub"]:
                result["sub"][parent_key] = {}
            result["sub"][parent_key][task] = data["count"]
        
        # Recurse into children
        if data["children"]:
            flatten_tree(data["children"], task, result)
    
    return result

def format_label(task, count, total_intervals, days):
    """Format label to show task name, percentage, and average hours per day."""
    percentage = (count / total_intervals) * 100
    # Each interval is 15 minutes, so multiply by 0.25 to get hours
    hours_per_day = (count * 0.25) / days
    return f"{task}\n({hours_per_day:.1f}h/day)"

def create_visualizations(tree, total_intervals):
    """Create and save pie chart and horizontal bar chart visualizations."""
    # Flatten the tree structure
    flat_data = flatten_tree(tree)
    
    # Calculate number of days based on total intervals
    # Assuming each day should have 96 intervals (24 hours * 4 intervals per hour)
    days = max(1, total_intervals / 96)
    
    # Create a figure with multiple subplots in a 3x2 grid
    fig = plt.figure(figsize=(20, 20))
    
    # 1. Main Pie Chart (top left)
    ax1 = plt.subplot(321)  # 3 rows, 2 cols, position 1
    main_tasks = flat_data["main"]
    
    # Filter out tasks with very small percentages (less than 1%)
    threshold = total_intervals * 0.01
    filtered_tasks = {k: v for k, v in main_tasks.items() if v >= threshold}
    other_count = sum(v for k, v in main_tasks.items() if v < threshold)
    if other_count > 0:
        filtered_tasks["other"] = other_count
    
    # Create main pie chart
    values = list(filtered_tasks.values())
    labels = [format_label(task, count, total_intervals, days) 
             for task, count in filtered_tasks.items()]
    
    wedges, texts, autotexts = ax1.pie(values, labels=labels,
                                      autopct='%1.1f%%',
                                      textprops={'fontsize': 8})
    ax1.set_title("Overall Time Distribution")
    
    # 2. Category Breakdown Pie Charts
    # Find the top 4 main categories (excluding sleep) to show their breakdowns
    top_categories = sorted([(k, v) for k, v in main_tasks.items() if k != "sleep"],
                          key=lambda x: x[1], reverse=True)[:4]
    
    # Create a pie chart for each top category
    subplot_positions = [322, 323, 324, 325]  # Positions in the 3x2 grid
    for idx, (category, total_count) in enumerate(top_categories):
        if category in flat_data["sub"]:
            ax = plt.subplot(subplot_positions[idx])
            subtasks = flat_data["sub"][category]
            total_category = sum(subtasks.values())
            
            # Handle direct category entries vs subcategories
            direct_category_count = main_tasks.get(category, 0) - total_category
            if direct_category_count > 0:
                subtasks = subtasks.copy()  # Create a copy to modify
                subtasks["other"] = direct_category_count
            
            # Sort subtasks by value
            sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1], reverse=True)
            
            # Create pie chart for this category
            values = [count for _, count in sorted_subtasks]
            labels = [format_label(task, count, total_count, days)
                     for task, count in sorted_subtasks]
            
            wedges, texts, autotexts = ax.pie(values, labels=labels,
                                             autopct='%1.1f%%',
                                             textprops={'fontsize': 8})
            total_hours = (total_count * 0.25) / days
            ax.set_title(f"{category.title()} Breakdown\nTotal: {total_hours:.1f}h/day")
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('time_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\nVisualizations have been saved to 'time_analysis.png'") 