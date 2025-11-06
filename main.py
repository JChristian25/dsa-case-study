# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data, group_students_by_section
from app.analytics.stats import compute_weighted_grades, calculate_distribution
from app.analytics.insights import compare_sections, find_hardest_topic
from app.reporting.exporter import export_to_csv
from app.reporting.plotting import plot_grade_histogram
from app.cli import run_menu
from rich.console import Console
from rich.table import Table

# --- Constants ---
CONFIG_PATH = "config.json"
# OUTPUT_REPORT_PATH = "output/at_risk_students.csv"


def main():
    console = Console()
    """Main function to run the data pipeline."""
    
    # 1. INGEST (JC's Task)
    print("Loading configuration...")
    config = load_config(CONFIG_PATH)
    
    print("Ingesting and validating student data...")
    all_students = read_csv_data(config['file_paths']['input_csv'])
    sections = group_students_by_section(all_students)

    # 2. TRANSFORM (Jeoffrey's Task)
    print("Calculating weighted grades...")
    grades = compute_weighted_grades(all_students, config['grade_weights'])
    # Checking if the logic of compute_weighted_grades is working correctly
    print(f"{"=" * 5} LIST OF STUDENTS {"=" * 5}")
    print(f"{'Student Name':19} {'Weighted Grade'}")
    for stud in grades:
        print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")

    print("Calculating weighted grades per section...")
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
        print(f"\n--- Section: {section_name} ---")
        print(f"{'Student Name':19} {'Weighted Grade'}")
        for stud in section_grades:
            print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")

    print("Calculating distribution...")
    distribution = calculate_distribution(grades, config['thresholds']['grade_letters'])
    # Checking if the logic of calculate_distribution is working correctly
    print(f"Total students: {len(all_students)}")
    print(f"{"=" * 5} GRADE LETTER COUNT {"=" * 5}")
    for key, val in distribution.items():
        print(f"{key + ':':^4} {val:^4} {'*' * val}")
        
    print("Calculating distribution per section...")
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
        section_distribution = calculate_distribution(section_grades, config['thresholds']['grade_letters'])
        print(f"\n--- Section: {section_name} ---")
        print(f"Total students: {len(students)}")
        print(f"{"=" * 5} GRADE LETTER COUNT {"=" * 5}")
        for key, val in section_distribution.items():
            print(f"{key + ':':^4} {val:^4} {'*' * val}")

    # 3. ANALYZE (Jeoffrey, Miles, JC's Tasks)
    print("Analyzing data...")
    sections = group_students_by_section(all_students)
    
    for section_name, students in sections.items():
        console.print(f"\n--- Analysis for Section: {section_name} ---", style="bold blue")
        find_hardest_topic(students)
        
    compare_sections(sections)
    
    # 4. REPORT (Daniel, Mary & Kirsten's Tasks)
    print("Generating reports...")
    for section_name, section_data in sections.items():
        if section_data:
            export_to_csv(
                section_data,
                f"{config['file_paths']['output_dir']}section_{section_name}_report.csv",
            )
        else:
            print(f"No data to export for section {section_name}")


if __name__ == "__main__":
    main()