# Holds outliers, improvements, comparisons
from typing import Any, Dict, List
from rich.console import Console
from stats import calculate_percentile

def find_outliers(students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    Q1 = calculate_percentile(students, 25)
    Q3 = calculate_percentile(students, 75)

    IQR = Q3 - Q1

    lower_fence = Q1 - (1.5 * IQR)
    upper_fence = Q3 + (1.5 * IQR)

    outliers = [
        s for s in students
        if s['weighted_grade'] < lower_fence 
        or s['weighted_grade'] > upper_fence
        
    ]

    return outliers
    



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

def find_hardest_topic(students: List[Dict[str, Any]]) -> None:
    console = Console()
    quiz_scores: Dict[str, List[int]] = {}

    # Project scores for each quiz into their own lists
    for student in students:
        for key, value in student.items():
            if key.lower().startswith('quiz') and isinstance(value, (int, float)):
                if key not in quiz_scores:
                    quiz_scores[key] = []
                quiz_scores[key].append(value)

    if not quiz_scores:
        console.print("No quiz data available to analyze.")
        return

    # Calculate the class average for each quiz
    quiz_averages = {quiz: sum(scores) / len(scores) for quiz, scores in quiz_scores.items()}

    # Find the quiz with the lowest average
    if not quiz_averages:
        console.print("Could not calculate quiz averages.")
        return
        
    hardest_quiz = min(quiz_averages, key=quiz_averages.get)
    lowest_avg = quiz_averages[hardest_quiz]

    # Report the insight and suggestion
    insight = f"The lowest-scoring activity was {hardest_quiz.replace('_', ' ').title()} ({lowest_avg:.1f}%)."
    suggestion = f"SUGGESTION: The topic for {hardest_quiz.replace('_', ' ').title()} was a class-wide weakness. Review this material."

    console.print(f"\n[bold]Hardest Topic Analysis:[/bold]")
    console.print(f"- {insight}")
    console.print(f"- {suggestion}")


# New: data-returning helpers for TUI tables
def get_quiz_averages(students: List[Dict[str, Any]]) -> List[Any]:
    quiz_scores: Dict[str, List[float]] = {}
    for student in students:
        for key, value in student.items():
            if key.lower().startswith('quiz') and isinstance(value, (int, float)):
                quiz_scores.setdefault(key, []).append(value)
    quiz_averages: Dict[str, float] = {k: (sum(v)/len(v) if v else 0.0) for k, v in quiz_scores.items()}
    quiz_counts: Dict[str, int] = {k: len(v) for k, v in quiz_scores.items()}
    if quiz_averages:
        hardest = min(quiz_averages, key=quiz_averages.get)
        lowest = quiz_averages[hardest]
    else:
        hardest, lowest = "", 0.0
    return [quiz_averages, quiz_counts, hardest, lowest]


def get_sections_quiz_averages(sections_data: Dict[str, List[Dict[str, Any]]]) -> List[Any]:
    # Discover quiz keys
    quiz_keys: List[str] = []
    for students in sections_data.values():
        if students:
            for key in students[0].keys():
                if key.startswith('quiz') and key not in quiz_keys:
                    quiz_keys.append(key)
    quiz_keys = sorted(quiz_keys)
    # Averages by section
    avg_by_section: Dict[str, Dict[str, float]] = {}
    for section, students in sections_data.items():
        per_quiz: Dict[str, float] = {}
        for quiz in quiz_keys:
            scores = [s.get(quiz) for s in students if s.get(quiz) is not None]
            per_quiz[quiz] = (sum(scores)/len(scores)) if scores else 0.0
        avg_by_section[section] = per_quiz
    # Lowest per quiz
    lowest: Dict[str, Dict[str, Any]] = {}
    for quiz in quiz_keys:
        section_min = min(avg_by_section.keys(), key=lambda s: avg_by_section[s][quiz]) if avg_by_section else ""
        lowest[quiz] = {"section": section_min, "avg": (avg_by_section[section_min][quiz] if section_min else 0.0)}
    return [avg_by_section, quiz_keys, lowest]