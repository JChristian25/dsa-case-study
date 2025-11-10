# Holds the 'export to CSV' logic
import csv
from typing import Any, Dict, List

import csv

students_csv_data = []

thresholds = {
    "at_risk_cutoff": 70.0
}

def export_to_csv(data: List[Dict[str, Any]], filepath: str):
    if not data:
        print("No data to export.")
        return

    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = data[0].keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(data)
    print(f"Data exported successfully to {filepath}")

def mark_at_risk(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Returns only the students who are below cutoff (at-risk)."""
    cutoff = thresholds["at_risk_cutoff"]
    at_risk = []

    for student in data:
        grade = student.get("weighted_grade")
        if grade is not None and float(grade) < cutoff:
            at_risk.append(student)

    return at_risk


def print_at_risk(at_risk: List[Dict[str, Any]]):
    cutoff = thresholds["at_risk_cutoff"]

    print(f"\nAT RISK STUDENTS (Below {cutoff:.1f})")
    if not at_risk:
        print("No students are at risk.\n")
        return

    for student in at_risk:
        print(f"{student['student_id']} - {student['last_name']}, {student['first_name']} "
              f", Section: {student['section']} , Weighted Grade: {student.get('weighted_grade')}")
    print()

# backend
at_risk_students = mark_at_risk(students_csv_data)

# front end display
print_at_risk(at_risk_students)

# export
filepath = input("Enter CSV filename for AT RISK students (example: at_risk_students.csv): ")
export_to_csv(at_risk_students, filepath)