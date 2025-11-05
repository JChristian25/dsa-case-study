# Holds outliers, improvements, comparisons
from typing import Any, Dict, List
from rich.console import Console

def find_outliers(students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    pass

def generate_improvement_insights(students: List[Dict[str, Any]]) -> List[str]:
    pass

def compare_sections(sections_data: Dict[str, List[Dict[str, Any]]]) -> None:
    console = Console()
    average_scores = {}
    all_quiz_keys = []
    # First, find all unique quiz keys across all sections using a list
    for students in sections_data.values():
        if students:
            for key in students[0].keys():
                if key.startswith('quiz') and key not in all_quiz_keys:
                    all_quiz_keys.append(key)
    
    sorted_quiz_keys = sorted(all_quiz_keys)
    # Calculate average scores for each section
    for section_name, students in sections_data.items():
        section_averages = {}
        for quiz_key in sorted_quiz_keys:
            scores = [student.get(quiz_key) for student in students if student.get(quiz_key) is not None]
            if scores:
                section_averages[quiz_key] = sum(scores) / len(scores)
            else:
                section_averages[quiz_key] = 0
        average_scores[section_name] = section_averages
    # Generate and print insights from the average scores
    insights = []
    if len(sections_data) > 1:
        for quiz_key in sorted_quiz_keys:
            # Find the section with the lowest average for the current quiz
            lowest_section = min(average_scores, key=lambda s: average_scores[s][quiz_key])
            lowest_avg = average_scores[lowest_section][quiz_key]
            # Generate comparison insight string
            comparison_parts = [f"{section}'s average for {quiz_key.replace('_', ' ').title()} was {average_scores[section][quiz_key]:.0f}%"
                                for section in sorted(average_scores.keys())]
            insight_str = ", ".join(comparison_parts)
            insights.append(f"For {quiz_key.replace('_', ' ').title()}, {insight_str}.")
            # Add a specific note about the lowest score
            insights.append(f"The lowest average for {quiz_key.replace('_', ' ').title()} was in {lowest_section} with {lowest_avg:.0f}%.")
    if insights:
        section_names = ", ".join(sorted(sections_data.keys()))
        console.print(f"\nComparing Sections: {section_names}\n")
        console.print("[bold]Key Insights:[/bold]")
        for insight in insights:
            console.print(f"- {insight}")