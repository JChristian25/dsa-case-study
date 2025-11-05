# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data, group_students_by_section
from app.analytics.stats import compute_weighted_grades, calculate_distribution
from app.analytics.insights import compare_sections
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


    # 2. TRANSFORM (Jeoffrey's Task)
    # print("Calculating weighted grades...")
    

    # 3. ANALYZE (Jeoffrey, Miles, JC's Tasks)
    print("Analyzing data...")
    sections = group_students_by_section(all_students)
    compare_sections(sections)
    
    # 4. REPORT (Daniel, Mary & Kirsten's Tasks)
    # print("Generating reports...")
    
    # print("\n--- Academic Insights ---")   
    
    # print(f"\nSuccessfully exported at-risk report to {OUTPUT_REPORT_PATH}")


if __name__ == "__main__":
    main()