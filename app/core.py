# Holds ingest, validation, config loading
import csv
import json
from typing import Any, Dict, List

def load_config(filepath: str) -> Dict[str, Any]:
    """Loads configuration from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def read_csv_data(filepath: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
    records = []
    required_columns = config.get("columns", {}).get("required", [])
    numeric_columns = list(config.get("columns", {}).get("numeric", []))
    for _auto_numeric_field in ["midterm", "final", "attendance_percent"]:
        if _auto_numeric_field not in numeric_columns:
            numeric_columns.append(_auto_numeric_field)

    with open(filepath, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i, row in enumerate(reader, start=2):  # Start from line 2 for error reporting
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}

            # Validate required fields
            if not all(row.get(col) for col in required_columns):
                print(f"Warning: Skipping row {i} due to missing required field(s).")
                continue

            # Process and validate numeric fields
            for col in numeric_columns:
                value = row.get(col)
                if value is None or value == '':
                    row[col] = None
                    continue
                try:
                    num = float(value)
                    if not (0 <= num <= 100):
                        print(f"Warning: Invalid value '{value}' in row {i}, column '{col}'. Setting to None.")
                        row[col] = None
                    else:
                        row[col] = num
                except (ValueError, TypeError):
                    print(f"Warning: Non-numeric value '{value}' in row {i}, column '{col}'. Setting to None.")
                    row[col] = None
            
            records.append(row)
    return records

# "Helper" function to para gumawa ng dictionary na may section as key and list of students as value
def group_students_by_section(students: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Groups a list of students by their section."""
    sections: Dict[str, List[Dict[str, Any]]] = {}
    for student in students:
        section = student.get('section')
        if section:
            if section not in sections:
                sections[section] = []
            sections[section].append(student)
    return sections


def insert_student(
    sections: Dict[str, List[Dict[str, Any]]], student: Dict[str, Any]
) -> None:
    section = student.get("section")
    if section:
        if section not in sections:
            sections[section] = []
        sections[section].append(student)


def delete_student(
    sections: Dict[str, List[Dict[str, Any]]], student_id: str
) -> bool:
    for section_list in sections.values():
        student_to_remove_index = -1
        for i, student in enumerate(section_list):
            if student.get("student_id") == student_id:
                student_to_remove_index = i
                break
        if student_to_remove_index != -1:
            del section_list[student_to_remove_index]
            return True
    return False

def sort_students(
    students: List[Dict[str, Any]], sort_by: str, reverse: bool = False
) -> List[Dict[str, Any]]:
    def get_sort_key(student: Dict[str, Any]):
        if sort_by in ['last_name', 'first_name', 'section', 'student_id']:
            return student.get(sort_by, "")
        else:
            return student.get(sort_by, 0) 
    sorted_list = sorted(students, key=get_sort_key, reverse=reverse)
    
    return sorted_list
