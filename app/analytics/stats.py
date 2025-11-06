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
                selected_stud[n] = 0
        # Calculating the weighed grade
        weighted_grade = (
            q_avr * weight['quizzes_total'] +
            selected_stud['midterm'] * weight['midterm'] +
            selected_stud['final'] * weight['final'] +
            selected_stud['attendance_percent'] * weight['attendance']
        )
        # Adding the 'weighted_grade' to selected stud
        selected_stud['weighted_grade'] = round(weighted_grade, 2)
        # Adding the selected student to placeholder
        stud_w_weighted_grade.append(selected_stud)
    return stud_w_weighted_grade

def calculate_distribution(students: List[Dict[str, Any]], thresholds: Dict[str, int]) -> Dict[str, int]:
    # Creating placeholder for students with grade evaluation
    students_with_gradeletter: Dict[str, int] = {}
    # Initializing the Dictionary for grade evaluation counter
    key = list(thresholds.keys())
    key.append('-D') # For students who doesn't meet the thresholds (below D)
    grade_eval_counter = {key:0 for key in key}
    # Processing students...
    for stud in students:
        # Checking what's the grade evaluation on a student then count
        if thresholds['A'] <= round(stud['weighted_grade']):
            grade_eval_counter['A'] += 1
        elif thresholds['B'] <= round(stud['weighted_grade']) < thresholds['A']:
            grade_eval_counter['B'] += 1
        elif thresholds['C'] <= round(stud['weighted_grade']) < thresholds['B']:
            grade_eval_counter['C'] += 1
        elif thresholds['D'] <= round(stud['weighted_grade']) < thresholds['C']:
            grade_eval_counter['D'] += 1
        elif thresholds['D'] > round(stud['weighted_grade']):
            grade_eval_counter['-D'] += 1
    return grade_eval_counter

def calculate_percentile(students: List[Dict[str, Any]], percentile: int) -> float | None:
    pass

def apply_grade_curve(students: List[Dict[str, Any]], method: str = "flat", value: float = 0) -> List[Dict[str, Any]]:
    pass

def _get_grade(student: Dict[str, Any]) -> float:
    """Helper function to get a student's grade, defaulting to 0."""
    return student.get("weighted_grade", 0)

def get_top_n_students(students: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    sorted_students = sorted(students, key=_get_grade, reverse=True)
    top_students = sorted_students[:n]
    return top_students

def get_bottom_n_students(students: List[Dict[str, Any]], n: int) -> List[Dict[str, Any]]:
    sorted_students = sorted(students, key=_get_grade)
    bottom_students = sorted_students[:n]
    return bottom_students

def get_average_grade(students: List[Dict[str, Any]]) -> float:
    if not students:
        return 0.0
    total_grade = 0.0
    for student in students:
        grade = student.get("weighted_grade", 0)
        total_grade += grade
    number_of_students = len(students)
    average_grade = total_grade / number_of_students
    return average_grade