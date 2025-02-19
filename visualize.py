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

def create_visualizations(tree, total_intervals):
    """Create and save pie chart and horizontal bar chart visualizations."""
    # Flatten the tree structure
    flat_data = flatten_tree(tree)
    
    # Create a figure with two subplots side by side
    fig = plt.figure(figsize=(20, 10))
    
    # 1. Pie Chart (left subplot)
    ax1 = fig.add_subplot(121)
    main_tasks = flat_data["main"]
    
    # Filter out tasks with very small percentages (less than 1%)
    threshold = total_intervals * 0.01
    filtered_tasks = {k: v for k, v in main_tasks.items() if v >= threshold}
    other_count = sum(v for k, v in main_tasks.items() if v < threshold)
    if other_count > 0:
        filtered_tasks["other"] = other_count
    
    # Create pie chart
    values = list(filtered_tasks.values())
    labels = list(filtered_tasks.keys())
    percentages = [v/total_intervals*100 for v in values]
    
    wedges, texts, autotexts = ax1.pie(percentages, labels=labels, autopct='%1.1f%%',
                                      textprops={'fontsize': 8})
    ax1.set_title("Overall Time Distribution")
    
    # 2. Horizontal Bar Chart (right subplot)
    ax2 = fig.add_subplot(122)
    
    # Find the top 3 main categories (excluding sleep) to show their breakdowns
    top_categories = sorted([(k, v) for k, v in main_tasks.items() if k != "sleep"],
                          key=lambda x: x[1], reverse=True)[:3]
    
    # Prepare data for horizontal bar chart
    all_bars = []
    all_labels = []
    y_positions = []
    current_y = 0
    
    for category, _ in top_categories:
        if category in flat_data["sub"]:
            subtasks = flat_data["sub"][category]
            total_category = sum(subtasks.values())
            
            # Sort subtasks by value
            sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1], reverse=True)
            
            for subtask, count in sorted_subtasks:
                percentage = (count / total_category) * 100
                all_bars.append(percentage)
                all_labels.append(f"{category}: {subtask}")
                y_positions.append(current_y)
                current_y += 1
            
            # Add space between categories
            current_y += 1
    
    # Create horizontal bar chart
    ax2.barh(y_positions, all_bars)
    ax2.set_yticks(y_positions)
    ax2.set_yticklabels(all_labels, fontsize=8)
    ax2.set_xlabel("Percentage within Category")
    ax2.set_title("Breakdown of Top 3 Categories")
    
    # Adjust layout and save
    plt.tight_layout()
    plt.savefig('time_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\nVisualizations have been saved to 'time_analysis.png'") 