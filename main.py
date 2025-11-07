# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data, group_students_by_section, insert_student, delete_student, sort_students
from app.analytics.stats import compute_weighted_grades, calculate_distribution, get_top_n_students, get_bottom_n_students, get_average_grade, apply_grade_curve
from app.analytics.insights import (
    compare_sections,  # legacy print version
    find_hardest_topic,  # legacy print version
    get_quiz_averages,
    get_sections_quiz_averages,
)
from app.reporting.exporter import export_to_csv
from app.reporting.tables import (
    build_student_table,
    build_distribution_table,
    build_section_summary_table,
    build_rank_table,
    build_curve_table,
    build_hardest_topic_table,
    build_quiz_comparison_table,
)
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
    # Overall roster table
    console.print(build_student_table(all_students, title="Overall Roster", at_risk_cutoff=config['thresholds']['at_risk_cutoff']))
    
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
    
    #calculate weighted grades per section (tables)
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
    console.print(build_student_table(section_grades, title=f"Section: {section_name}", at_risk_cutoff=config['thresholds']['at_risk_cutoff']))
    
    # sort students in a section by weighted grade
    print("\n--- Sorting students by weighted grade (descending) ---")
    for section_name, students in sections.items():
        sorted_by_grade = sort_students(students, sort_by='weighted_grade', reverse=True)
    console.print(build_student_table(sorted_by_grade, title=f"Section: {section_name} (Sorted by Grade desc)", at_risk_cutoff=config['thresholds']['at_risk_cutoff']))

    # sort students in a section by last name
    print("\n--- Sorting students by last name (ascending) ---")
    for section_name, students in sections.items():
        sorted_by_name = sort_students(students, sort_by='last_name')
    console.print(build_student_table(sorted_by_name, title=f"Section: {section_name} (Sorted by Last Name asc)", at_risk_cutoff=config['thresholds']['at_risk_cutoff']))
            
    # sort students in a section by first name
    print("\n--- Sorting students by first name (ascending) ---")
    for section_name, students in sections.items():
        sorted_by_name = sort_students(students, sort_by='first_name')
    console.print(build_student_table(sorted_by_name, title=f"Section: {section_name} (Sorted by First Name asc)", at_risk_cutoff=config['thresholds']['at_risk_cutoff']))
            
    # project: get top N students per section
    N = 3
    print(f"\n--- Top {N} Students per Section ---")
    for section_name, students in sections.items():
        top_students = get_top_n_students(students, N)
        rows = [dict(rank=i+1, **s) for i, s in enumerate(top_students)]
        console.print(build_rank_table(rows, title=f"Top {N} - {section_name}"))
            
    # project: get bottom N students per section
    print(f"\n--- Bottom {N} Students per Section ---")
    for section_name, students in sections.items():
        bottom_students = get_bottom_n_students(students, N)
        rows = [dict(rank=i+1, **s) for i, s in enumerate(bottom_students)]
        console.print(build_rank_table(rows, title=f"Bottom {N} - {section_name}"))
            
    # project: rank students overall
    
    # project: rank students per section
    
    # project: get average grade per section
    print("\n--- Average Grade per Section ---")
    averages = {section_name: get_average_grade(students) for section_name, students in sections.items()}
    console.print(build_section_summary_table(sections, averages, title="Average Grade per Section"))
    
    ## == ANALYZE == ##
    # calculate distribution of grades overall and per section
    distribution = calculate_distribution(all_students, config['thresholds']['grade_letters'])
    console.print(build_distribution_table(distribution, total=len(all_students), title="Overall Grade Distribution"))
        
    for section_name, students in sections.items():
        section_grades = compute_weighted_grades(students, config['grade_weights'])
        section_distribution = calculate_distribution(section_grades, config['thresholds']['grade_letters'])
        console.print(build_distribution_table(section_distribution, total=len(students), title=f"Grade Distribution - {section_name}"))
    
    # calculate percentiles overall and per section
    
    # find outliers per section
    
    # find outliers overall
    
        
    # analyze data: hardest topic per section (table) and quiz comparison across sections
    for section_name, students in sections.items():
        quiz_data = get_quiz_averages(students)
        quiz_avgs = quiz_data[0]
        quiz_counts = quiz_data[1]
        hardest_quiz = quiz_data[2]
        console.print(build_hardest_topic_table(quiz_avgs, quiz_counts, hardest_quiz, title=f"Hardest Topic - {section_name}"))

    sections_quiz_data = get_sections_quiz_averages(sections)
    avg_by_section = sections_quiz_data[0]
    quiz_keys = sections_quiz_data[1]
    lowest_per_quiz = sections_quiz_data[2]
    console.print(build_quiz_comparison_table(avg_by_section, quiz_keys, lowest_per_quiz, title="Quiz Averages Comparison"))
    
    # apply grade curve
    all_students = apply_grade_curve(all_students, method="flat", value=5.0)
    print("5-point flat curve applied successfully.")
    console.print(build_curve_table(all_students[:5], title="Curve Preview (flat +5)"))
    
    # Apply a normalize-to-100 curve
    all_students = apply_grade_curve(all_students, method="normalize", value=100.0)
    print("Normalize-to-100 curve applied successfully.")
    console.print(build_curve_table(all_students[:5], title="Curve Preview (normalize to 100)"))

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