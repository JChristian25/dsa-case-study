# Holds avg, median, weighted_grade
import math
from typing import Any, Dict, List

def compute_weighted_grades(students: List[Dict[str, Any]], weight: Dict[str, float]) -> List[Dict[str, Any]]:
    # Initializing keys
    keys = (
        ('quiz1', 'quiz2', 'quiz3', 'quiz4', 'quiz5'),
        ('midterm', 'final', 'attendance_percent')
    )
    # Creating placeholder for students along with weighted grade
    stud_w_weighted_grade = []
    # Processing the students...
    for stud in students:
        # Copies data of selected stud
        selected_stud = stud.copy()
        # Transforming None as 0 while calculating the average of quizzes
        q_scores = []
        for n in keys[0]:
            if stud[n] is None:
                q_scores.append(0)
                continue
            q_scores.append(stud[n])
        q_avr = round(sum(q_scores) / len(keys[0]), 2)
        # Transforming None as 0 for final, midterm, and attendance_percent
        for n in keys[1]:
            if stud[n] is None:
                stud[n] = 0
        # Calculating the weighed grade
        weighted_grade = (
            q_avr * weight['quizzes_total'] +
            stud['midterm'] * weight['midterm'] +
            stud['final'] * weight['final'] +
            stud['attendance_percent'] * weight['attendance']
        )
        # Adding the 'weighted_grade' to selected stud
        selected_stud['weighted_grade'] = round(weighted_grade, 2)
        # Adding the selected student to placeholder
        stud_w_weighted_grade.append(selected_stud)
    return stud_w_weighted_grade

def calculate_distribution(students: List[Dict[str, Any]], thresholds: Dict[str, int]) -> Dict[str, int]:
    pass

def calculate_percentile(students: List[Dict[str, Any]], percentile: int) -> float | None:
    pass

def apply_grade_curve(students: List[Dict[str, Any]], method: str = "flat", value: float = 0) -> List[Dict[str, Any]]:
    pass