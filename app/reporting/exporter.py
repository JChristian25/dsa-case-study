# Holds the 'export to CSV' logic
import csv
from typing import Any, Dict, List

import csv

students_csv_data = []

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

