# Holds the Matplotlib histogram logic
from typing import Any, Dict, List
import matplotlib
import os
import sys
from datetime import datetime

# Detect if running in headless environment (no display)
def _is_display_available():
    """Check if a display is available for showing plots."""
    if sys.platform == 'win32':
        return True  # Windows usually has display
    # Linux/Unix: check for DISPLAY environment variable
    return os.environ.get('DISPLAY') is not None

# Set backend based on environment
if not _is_display_available():
    matplotlib.use('Agg')  # Use non-interactive backend for headless

import matplotlib.pyplot as plt

# Function to plot histogram for any column
def plot_grade_histogram(students: List[Dict[str, Any]], key: str, title: str = None, save_path: str = None, show_plot: bool = None):
    values = [s.get(key) for s in students if s.get(key) is not None]

    if title is None:
        title = f"Distribution of {key.replace('_', ' ').capitalize()}"

    # Set color depending on type
    if key.startswith("quiz"):
        color = "skyblue"
    elif key == "midterm":
        color = "yellow"
    elif key == "final":
        color = "orange"
    elif key == "weighted_grade":
        color = "salmon"
    elif "attendance" in key.lower():
        color = "lightgreen"
    else:
        color = "gray"

    plt.figure(figsize=(8, 5))
    plt.hist(values, bins=10, edgecolor='black', color=color)
    plt.title(title)
    plt.xlabel("Score")
    plt.ylabel("Number of Students")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Determine whether to show or save
    if show_plot is None:
        show_plot = _is_display_available()
    
    # Always save the file
    if save_path:
        filename = save_path
    else:
        # Auto-generate filename
        os.makedirs("output/plots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"output/plots/{key}_{timestamp}.png"
    
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    
    # Show plot if display is available
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return filename


# Function to plot combined histogram for multiple columns with distinct colors
def plot_combined_histogram(students: List[Dict[str, Any]], keys: List[str], title: str = None, save_path: str = None, show_plot: bool = None):
    plt.figure(figsize=(12, 6))

    # Assign specific colors
    color_mapping = {
        "quiz1": "skyblue",
        "quiz2": "lightcoral",
        "quiz3": "lightseagreen",
        "quiz4": "gold",
        "quiz5": "orchid",
        "midterm": "yellow",
        "final": "orange",
        "weighted_grade": "salmon",
        "attendance_percent": "lightgreen"
    }

    # Plot each column
    for key in keys:
        values = [s.get(key) for s in students if s.get(key) is not None]
        plt.hist(values, bins=10, alpha=0.6, edgecolor='black', label=key.replace('_', ' ').capitalize(),
                 color=color_mapping.get(key, "gray"))

    if title is None:
        title = "Combined Histogram"

    plt.title(title)
    plt.xlabel("Score")
    plt.ylabel("Number of Students")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend()
    
    # Determine whether to show or save
    if show_plot is None:
        show_plot = _is_display_available()
    
    # Always save the file
    if save_path:
        filename = save_path
    else:
        # Auto-generate filename
        os.makedirs("output/plots", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = title.replace(" ", "_").replace("/", "-") if title else "combined"
        filename = f"output/plots/{safe_title}_{timestamp}.png"
    
    plt.savefig(filename, bbox_inches='tight', dpi=300)
    
    # Show plot if display is available
    if show_plot:
        plt.show()
    else:
        plt.close()
    
    return filename
