# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data, group_students_by_section, insert_student, delete_student, sort_students
from app.analytics.stats import compute_weighted_grades, calculate_distribution, get_top_n_students, get_bottom_n_students, get_average_grade
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
    # The line `sections = group_students_by_section(all_students)` is creating a dictionary where the keys are the section names and the values are lists of students belonging to each section. This function is grouping the students based on their section, which allows for easier analysis and manipulation of student data within each section.
    sections = group_students_by_section(all_students)
    
    # insert student
        # insert student
    print("\n--- Inserting a new student ---")
    new_student = {
        'student_id': '2024-9999', 'last_name': 'Zzz', 'first_name': 'Alpha', 'section': 'BSIT-1A',
        'quiz1': 85, 'quiz2': 90, 'quiz3': 88, 'quiz4': 92, 'quiz5': 89,
        'midterm': 91, 'final': 93, 'attendance_percent': 95
    }
    
    # The new student needs a weighted grade before being added
    new_student_with_grade = compute_weighted_grades([new_student], config['grade_weights'])[0]
    insert_student(sections, new_student_with_grade)
    all_students.append(new_student_with_grade)
    print(f"Added {new_student_with_grade['first_name']} to section {new_student_with_grade['section']}.")
    
    # delete student
    print("\n--- Deleting a student ---")
    student_to_delete_id = '2022-0002'
    if delete_student(sections, student_to_delete_id):
        # Also remove from the main list
        all_students = [s for s in all_students if s.get('student_id') != student_to_delete_id]
        print(f"Successfully deleted student with ID {student_to_delete_id}.")
    else:
        print(f"Could not find student with ID {student_to_delete_id}.")
    
    #calculate weighted grades per section
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
        print(f"\n--- Section: {section_name} ---")
        print(f"{'Student Name':19} {'Weighted Grade'}")
        for stud in section_grades:
            print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")
    
    # sort students in a section by weighted grade
    print("\n--- Sorting students by weighted grade (descending) ---")
    for section_name, students in sections.items():
        sorted_by_grade = sort_students(students, sort_by='weighted_grade', reverse=True)
        print(f"\n--- Section: {section_name} (Sorted by Grade) ---")
        for stud in sorted_by_grade:
            print(f"{stud['first_name'] + ' ' + stud['last_name']:23} {stud['weighted_grade']:2.2f}")

    # sort students in a section by last name
    print("\n--- Sorting students by last name (ascending) ---")
    for section_name, students in sections.items():
        sorted_by_name = sort_students(students, sort_by='last_name')
        print(f"\n--- Section: {section_name} (Sorted by Last Name) ---")
        for stud in sorted_by_name:
            print(f"{stud['last_name']}, {stud['first_name']:15} {stud['weighted_grade']:2.2f}")
            
    # sort students in a section by first name
    print("\n--- Sorting students by last name (ascending) ---")
    for section_name, students in sections.items():
        sorted_by_name = sort_students(students, sort_by='first_name')
        print(f"\n--- Section: {section_name} (Sorted by Last Name) ---")
        for stud in sorted_by_name:
            print(f"{stud['last_name']}, {stud['first_name']:15} {stud['weighted_grade']:2.2f}")
            
    # project: get top N students per section
    N = 3
    print(f"\n--- Top {N} Students per Section ---")
    for section_name, students in sections.items():
        top_students = get_top_n_students(students, N)
        print(f"\n--- Section: {section_name} ---")
        for i, stud in enumerate(top_students):
            print(f"{i+1}. {stud['first_name'] + ' ' + stud['last_name']:21} {stud['weighted_grade']:2.2f}")
            
    # project: get bottom N students per section
    print(f"\n--- Bottom {N} Students per Section ---")
    for section_name, students in sections.items():
        bottom_students = get_bottom_n_students(students, N)
        print(f"\n--- Section: {section_name} ---")
        for i, stud in enumerate(bottom_students):
            print(f"{i+1}. {stud['first_name'] + ' ' + stud['last_name']:21} {stud['weighted_grade']:2.2f}")
            
    # project: rank students overall
    
    # project: rank students per section
    
    # project: get average grade per section
    print("\n--- Average Grade per Section ---")
    for section_name, students in sections.items():
        average_grade = get_average_grade(students)
        print(f"Section {section_name}: {average_grade:.2f}")
    
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
    
    # find outliers per section
    
    # find outliers overall
    
    # apply grade curve
    
    # analyze data: hardest topic per section, compare sections
    for section_name, students in sections.items():
        console.print(f"\n--- Analysis for Section: {section_name} ---", style="bold blue")
        find_hardest_topic(students)
        
    compare_sections(sections)
    
    ## == REPORT == ##
    # reporting: export to csv per section, plot histograms
    
    # export files
    for section_name, section_data in sections.items():
        if section_data:
            export_to_csv(
                section_data,
                f"{config['file_paths']['output_dir']}section_{section_name}_report.csv",
            )
        else:
            print(f"No data to export for section {section_name}")
            
    # plot histograms
    
    # report at-risk students

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        run_menu()
    else:
        main()