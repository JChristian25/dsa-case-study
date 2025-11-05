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
