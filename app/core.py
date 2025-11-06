# Holds ingest, validation, config loading
import csv
import json
from typing import Any, Dict, List

def load_config(filepath: str) -> Dict[str, Any]:
    """Loads configuration from a JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def read_csv_data(filepath: str) -> List[Dict[str, Any]]:
    # Initialize empty list to store processed records
    records = []    
    # Open CSV file and create DictReader for column-based access
    with open(filepath, newline='') as csvfile: 
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Strip whitespace from string values while preserving other types
            row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
            # Process each field in the row
            for key in row:
                # Skip processing for non-numeric fields (student info and section)
                if key not in ['student_id', 'last_name', 'first_name', 'section']:
                    value = row[key]
                    # Set empty or None values to None
                    if value == '' or value is None:
                        row[key] = None
                        continue
                    try:
                        # Convert to float and validate range (0-100 for grades)
                        num = float(value)
                        if 0 <= num <= 100:
                            row[key] = num
                        else: # Invalid range, set to None
                            row[key] = None
                    except ValueError:
                        # Non-numeric value, set to None
                        row[key] = None
            # Add processed row to records list
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
