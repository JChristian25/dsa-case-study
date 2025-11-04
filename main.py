# --- Imports from your custom modules ---
from app.core import load_config, read_csv_data
from app.analytics.stats import compute_weighted_grades, calculate_distribution
from app.analytics.insights import find_outliers, generate_improvement_insights
from app.reporting.exporter import export_to_csv
from app.reporting.plotting import plot_grade_histogram
from app.cli import run_menu

# --- Constants ---
CONFIG_PATH = "config.json"
DATA_PATH = "data/input.csv"
OUTPUT_REPORT_PATH = "output/at_risk_students.csv"

def main():
    """Main function to run the data pipeline."""
    
    # 1. INGEST (JC's Task)
    print("Loading configuration...")
    
    print("Ingesting and validating student data...")

    # 2. TRANSFORM (Jeoffrey's Task)
    print("Calculating weighted grades...")

    # 3. ANALYZE (Jeoffrey, Miles, JC's Tasks)
    print("Analyzing data...")
    
    # 4. REPORT (Daniel, Mary & Kirsten's Tasks)
    print("Generating reports...")
    
    print("\n--- Academic Insights ---")   
    
    print(f"\nSuccessfully exported at-risk report to {OUTPUT_REPORT_PATH}")


if __name__ == "__main__":
    main()