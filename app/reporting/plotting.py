# Holds the Matplotlib histogram logic
from typing import Any, Dict, List
import matplotlib.pyplot as plt

# Function to plot histogram for any column
def plot_grade_histogram(students: List[Dict[str, Any]], key: str, title: str = None):
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
    plt.show()


# Function to plot combined histogram for multiple columns with distinct colors
def plot_combined_histogram(students: List[Dict[str, Any]], keys: List[str], title: str = None):
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
    plt.show()


# Sample Data
raw_data = [
    ["S001","Smith","John","BSIT 2-2",85.5,"",78.5,92.0,88.0,85.0,90.5,95.0],
    ["S002","Johnson","Emily","BSIT 2-1",92.0,95.0,89.5,91.0,93.5,88.5,94.0,98.0],
    ["S003","Williams","Michael","BSIT 2-2",75.0,70.5,68.0,72.0,74.5,70.0,75.5,85.0],
    ["S004","Brown","Sarah","BSIT 2-2",95.5,98.0,96.5,94.0,97.0,95.0,98.5,100.0],
    ["S005","Jones","David","BSIT 2-1",65.0,60.5,62.0,58.5,63.0,60.0,65.5,75.0]
]

# Convert to list of dicts
all_students = []
for row in raw_data:
    student = {
        "student_id": row[0],
        "last_name": row[1],
        "first_name": row[2],
        "section": row[3],
        "quiz1": row[4] if row[4] != "" else None,
        "quiz2": row[5] if row[5] != "" else None,
        "quiz3": row[6] if row[6] != "" else None,
        "quiz4": row[7] if row[7] != "" else None,
        "quiz5": row[8] if row[8] != "" else None,
        "midterm": row[9] if row[9] != "" else None,
        "final": row[10] if row[10] != "" else None,
        "attendance_percent": row[11] if row[11] != "" else None,
        "weighted_grade": (
            sum([
                row[4] if row[4] != "" else 0,
                row[5] if row[5] != "" else 0,
                row[6] if row[6] != "" else 0,
                row[7] if row[7] != "" else 0,
                row[8] if row[8] != "" else 0,
            ])*0.1 + (row[9] if row[9] != "" else 0)*0.3 + (row[10] if row[10] != "" else 0)*0.4
        )
    }
    all_students.append(student)

# Individual Histograms
plot_grade_histogram(all_students, "weighted_grade", "Weighted Grade Distribution")
for quiz in ["quiz1","quiz2","quiz3","quiz4","quiz5"]:
    plot_grade_histogram(all_students, quiz)
plot_grade_histogram(all_students, "midterm")
plot_grade_histogram(all_students, "final")
plot_grade_histogram(all_students, "attendance_percent")

# Combined Histograms
plot_combined_histogram(all_students, ["quiz1","quiz2","quiz3","quiz4","quiz5"], "Quiz Scores Distribution")
plot_combined_histogram(all_students, ["midterm","final"], "Assessment Scores Distribution")
plot_combined_histogram(all_students, ["attendance_percent"], "Attendance Distribution")
plot_combined_histogram(all_students, ["quiz1","quiz2","quiz3","quiz4","quiz5",
                                       "midterm","final","weighted_grade"], "All Scores including Weighted Grade")