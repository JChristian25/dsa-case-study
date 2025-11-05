# Holds avg, median, weighted_grade
import math
from typing import Any, Dict, List

sample_students_data: List[Dict[str, any]] = [
    {'student_id': 'S001', 'last_name': 'Smith', 'first_name': 'John', 'section': '90', 'quiz1': 85.5, 'quiz2': None, 'quiz3': 78.5, 'quiz4': 92.0, 'quiz5': 88.0, 'midterm': 85.0, 'final': 90.5, 'attendance_percent': 95.0},
    {'student_id': 'S002', 'last_name': 'Johnson', 'first_name': 'Emily', 'section': '1', 'quiz1': 92.0, 'quiz2': 95.0, 'quiz3': 89.5, 'quiz4': 91.0, 'quiz5': 93.5, 'midterm': 88.5, 'final': 94.0, 'attendance_percent': 98.0},
    {'student_id': 'S003', 'last_name': 'Williams', 'first_name': 'Michael', 'section': '2', 'quiz1': 75.0, 'quiz2': 70.5, 'quiz3': 68.0, 'quiz4': 72.0, 'quiz5': 74.5, 'midterm': 70.0, 'final': 75.5, 'attendance_percent': 85.0},
    {'student_id': 'S004', 'last_name': 'Brown', 'first_name': 'Sarah', 'section': '2', 'quiz1': 95.5, 'quiz2': 98.0, 'quiz3': 96.5, 'quiz4': 94.0, 'quiz5': 97.0, 'midterm': 95.0, 'final': 98.5, 'attendance_percent': 100.0},
    {'student_id': 'S005', 'last_name': 'Jones', 'first_name': 'David', 'section': '1', 'quiz1': 65.0, 'quiz2': 60.5, 'quiz3': 62.0, 'quiz4': 58.5, 'quiz5': 63.0, 'midterm': 60.0, 'final': 65.5, 'attendance_percent': 75.0},
    {'student_id': 'S006', 'last_name': 'Garcia', 'first_name': 'Maria', 'section': '3', 'quiz1': 88.0, 'quiz2': 85.5, 'quiz3': 90.0, 'quiz4': 87.5, 'quiz5': 89.0, 'midterm': 88.5, 'final': 91.0, 'attendance_percent': 92.0},
    {'student_id': 'S007', 'last_name': 'Martinez', 'first_name': 'Carlos', 'section': '3', 'quiz1': 78.5, 'quiz2': 82.0, 'quiz3': 80.5, 'quiz4': 79.0, 'quiz5': 81.5, 'midterm': 80.0, 'final': 83.5, 'attendance_percent': 88.0}
]

def compute_weighted_grades(students: List[Dict[str, Any]], weights: Dict[str, float]) -> List[Dict[str, Any]]:
    for stud in students:
        # Initializing keys for quiz1 - quiz5
        qkeys = ('quiz1', 'quiz2', 'quiz3', 'quiz4', 'quiz5')
        # Creating dict placeholder for stud
        new_stud = {}
        # Calculating the average of quizzes, treating None as 0
        q_scores = []
        for n in qkeys:
            if stud[n] is None:
                q_scores.append(0)
                continue
            q_scores.append(stud[n])
        q_avr = round(sum(q_scores) / len(qkeys), 2)
        # Inserting q_avr after 'quiz5'
        for key in stud:
            if key == 'midterm':
                new_stud['quizzes_average'] = q_avr
            new_stud[key] = stud[key]
        # Calculating the weighted_grade
        weighted_grade = (
            q_avr * weights['qavr_w'] +
            stud['midterm'] * weights['mid_w'] +
            stud['final'] * weights['fin_w'] +
            stud['attendance_percent'] * weights['att_pcnt_w']
        )
        # Adding the 'weighted_grade' to the dict placeholder
        new_stud['weighted_grade'] = round(weighted_grade, 2)
        # Replacing original stud dict with dict placeholder
        stud.clear()
        for k, v in new_stud.items():
            stud[k] = v
    return students

def calculate_distribution(students: List[Dict[str, Any]], thresholds: Dict[str, int]) -> Dict[str, int]:
    pass

def calculate_percentile(students: List[Dict[str, Any]], percentile: int) -> float | None:
    pass

def apply_grade_curve(students: List[Dict[str, Any]], method: str = "flat", value: float = 0) -> List[Dict[str, Any]]:
    pass

grade_weight: Dict[str, float] = {
    'qavr_w' : 0.15,
    'mid_w' : 0.4,
    'fin_w' : 0.4,
    'att_pcnt_w' : 0.05
    }
sample_students_data = compute_weighted_grades(sample_students_data, grade_weight)
print("    ====== LIST OF STUDENTS ======")
print(f"{'Student Name':19} {'Weighted Grade'}")
for stud in sample_students_data:
    print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")
    
