# Holds the Matplotlib histogram logic
from typing import Any, Dict, List
import matplotlib.pyplot as plt

def plot_grade_histogram(students: List[Dict[str, Any]], title: str):
    grades = [s.get("weighted_grade", 0) for s in students if "weighted_grade" in s]

    plt.figure(figsize=(8, 5))
    plt.hist(grades, bins=10, edgecolor='black', color='skyblue')

    plt.title('Distribution of Weighted Grades')
    plt.xlabel('Grade')
    plt.ylabel('Number of Students')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    plt.show()

    # Mock data for testing

mock_weighted_grades = [
    88.5, 91.2, 77.0, 58.1, 95.0, 72.3, 85.1, 66.9, 81.7, 90.5,
    79.2, 88.0, 62.5, 76.8, 92.3, 83.4, 70.1, 89.6, 68.7, 78.9,
    94.0, 81.3, 73.5, 86.2, 61.4, 97.8, 75.0, 82.9, 90.0, 69.8,
    84.5, 77.7, 91.8, 80.5, 64.2, 88.9, 72.0, 93.3, 79.8, 85.7
]

# Converting mock list into list of dicts to match function parameter

mock_students = [{"weighted_grade": g} for g in mock_weighted_grades]

#Calling the function
plot_grade_histogram(mock_students, "Mock Weighted Grade Distribution")


