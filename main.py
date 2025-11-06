# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data, group_students_by_section
from app.analytics.stats import compute_weighted_grades, calculate_distribution
from app.analytics.insights import compare_sections, find_hardest_topic
from app.reporting.exporter import export_to_csv
from app.reporting.plotting import plot_grade_histogram
from app.cli import run_menu
from rich.console import Console
from rich.table import Table
import sys

# --- Constants ---
CONFIG_PATH = "config.json"
# OUTPUT_REPORT_PATH = "output/at_risk_students.csv"

def main():
    console = Console()
    #load config
    config = load_config(CONFIG_PATH)
    ## == INGEST == ##
    #ingest data
    all_students = read_csv_data(config['file_paths']['input_csv'])
    
    ## == TRANSFORM == ##
    #transform data, get weighted grade
    all_students = compute_weighted_grades(all_students, config['grade_weights'])
    
    print(f"{'Student Name':19} {'Weighted Grade'}")
    for stud in all_students:
        print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")
    
    #create a dictionary of sections with students in each section
    sections = group_students_by_section(all_students)
    
    #calculate weighted grades per section
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
        print(f"\n--- Section: {section_name} ---")
        print(f"{'Student Name':19} {'Weighted Grade'}")
        for stud in section_grades:
            print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")
    
    ## == ANALYZE == ##
    # calculate distribution of grades overall and per section
    distribution = calculate_distribution(all_students, config['thresholds']['grade_letters'])
    print(f"Total students: {len(all_students)}")
    print(f"{"=" * 5} GRADE LETTER COUNT {"=" * 5}")
    for key, val in distribution.items():
        print(f"{key + ':':^4} {val:^4} {'*' * val}")
        
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
        section_distribution = calculate_distribution(section_grades, config['thresholds']['grade_letters'])
        print(f"\n--- Section: {section_name} ---")
        print(f"Total students: {len(students)}")
        print(f"{"=" * 5} GRADE LETTER COUNT {"=" * 5}")
        for key, val in section_distribution.items():
            print(f"{key + ':':^4} {val:^4} {'*' * val}")
    
    # calculate percentiles overall and per section
    
    # analyze data: hardest topic per section, compare sections
    for section_name, students in sections.items():
        console.print(f"\n--- Analysis for Section: {section_name} ---", style="bold blue")
        find_hardest_topic(students)
        
    compare_sections(sections)
    
    ## == REPORT == ##
    # reporting: export to csv per section, plot histograms
    for section_name, section_data in sections.items():
        if section_data:
            export_to_csv(
                section_data,
                f"{config['file_paths']['output_dir']}section_{section_name}_report.csv",
            )
        else:
            print(f"No data to export for section {section_name}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_menu()
    else:
        main()