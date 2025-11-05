# Holds the 'export to CSV' logic
import csv
from typing import Any, Dict, List

import csv

students_csv_data = []

def export_to_csv(data: List[Dict[str, Any]], filepath: str):
    with open(filepath, mode="w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data[0].keys())
        writer.writeheader()     
        writer.writerows(students_csv_data) 
    print(f"Data exported successfully to {filepath}")

export_to_csv(students_csv_data,"test/students_output.csv")
