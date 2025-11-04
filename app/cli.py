from typing import Any, Dict, List
from app.analytics.stats import calculate_distribution, calculate_percentile
from app.analytics.insights import find_outliers, generate_improvement_insights, compare_sections
from app.reporting.plotting import plot_grade_histogram, plot_grade_boxplot
from app.reporting.exporter import export_to_csv

def run_menu():
    pass