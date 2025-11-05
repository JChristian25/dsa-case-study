# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data
from app.analytics.stats import compute_weighted_grades, calculate_distribution
from app.analytics.insights import find_outliers, generate_improvement_insights, compare_sections
from app.reporting.exporter import export_to_csv
from app.reporting.plotting import plot_grade_histogram
from app.cli import run_menu
from rich.console import Console
from rich.table import Table

# --- Constants ---
CONFIG_PATH = "config.json"
# OUTPUT_REPORT_PATH = "output/at_risk_students.csv"

def _display_student_table(students):
    console = Console()
    table = Table(show_header=True, header_style="bold magenta")
    
    if students:
        # Assuming all students have the same keys
        headers = students[0].keys()
        for header in headers:
            table.add_column(header.replace("_", " ").title())
        
        # Add rows
        for student in students:
            table.add_row(*[str(value) for value in student.values()])
            
    console.print(table)

def main():
    """Main function to run the data pipeline."""
    
    # 1. INGEST (JC's Task)
    print("Loading configuration...")
    config = load_config(CONFIG_PATH)
    
    print("Ingesting and validating student data...")
    all_students = read_csv_data(config['file_paths']['input_csv'])


    # 2. TRANSFORM (Jeoffrey's Task)
    # print("Calculating weighted grades...")
    

    # 3. ANALYZE (Jeoffrey, Miles, JC's Tasks)
    print("Analyzing data...")
    scores = compare_sections(all_students)
    print("Section Scores:", scores)
    
    # 4. REPORT (Daniel, Mary & Kirsten's Tasks)
    # print("Generating reports...")
    
    # print("\n--- Academic Insights ---")   
    
    # print(f"\nSuccessfully exported at-risk report to {OUTPUT_REPORT_PATH}")


if __name__ == "__main__":
    main()