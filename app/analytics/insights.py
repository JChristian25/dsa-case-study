# Holds outliers, improvements, comparisons
"""Analytics insights for outliers, improvements, correlations, and comparisons.

Authors:
- John Christian Linaban
- John Miles Varca
"""

from typing import Any, Dict, List
from rich.console import Console
from app.analytics.stats import calculate_percentile

def find_outliers(students: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    Q1 = calculate_percentile(students, 25)
    Q3 = calculate_percentile(students, 75)
    if Q1 is None or Q3 is None:
        return []
    IQR = Q3 - Q1
    lower_fence = Q1 - (1.5 * IQR)
    upper_fence = Q3 + (1.5 * IQR)
    return [
        s for s in students
        if s.get('weighted_grade') is not None
        and (s['weighted_grade'] < lower_fence or s['weighted_grade'] > upper_fence)
    ]
    



def track_midterm_to_final_improvement(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    students_with_both = [
        s for s in students
        if s.get('midterm') is not None and s.get('final') is not None
    ]
    if not students_with_both:
        return {
            'total_students': 0,
            'counts': {'improved': 0, 'same': 0, 'declined': 0, 'declined_or_same': 0},
            'percentages': {'improved': 0.0, 'same': 0.0, 'declined': 0.0, 'declined_or_same': 0.0},
            'avg_improvement': 0.0,
            'avg_decline': 0.0,
            'suggestions': [],
        }
    improved = [s for s in students_with_both if s['final'] > s['midterm']]
    declined_or_same = [s for s in students_with_both if s['final'] <= s['midterm']]
    same = [s for s in students_with_both if s['final'] == s['midterm']]
    declined = [s for s in students_with_both if s['final'] < s['midterm']]
    total_students = len(students_with_both)
    improved_pct = (len(improved) / total_students) * 100
    same_pct = (len(same) / total_students) * 100
    declined_pct = (len(declined) / total_students) * 100
    declined_or_same_pct = (len(declined_or_same) / total_students) * 100
    improvements = [s['final'] - s['midterm'] for s in improved]
    avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
    declines = [s['midterm'] - s['final'] for s in declined]
    avg_decline = sum(declines) / len(declines) if declines else 0.0
    suggestions: List[str] = []
    if declined_or_same_pct >= 30:
        suggestions.append(
            f"The {declined_or_same_pct:.0f}% who didn't improve may need different strategies for cumulative exams."
        )
    if len(declined) > 0:
        suggestions.append(
            f"Provide additional resources or remediation for {len(declined)} students who declined."
        )
    if improved_pct < 50:
        suggestions.append("Less than half improved—review final exam prep and study sessions.")
    elif improved_pct >= 70:
        suggestions.append("Excellent improvement rate—continue current teaching and review strategies.")
    return {
        'total_students': total_students,
        'counts': {
            'improved': len(improved),
            'same': len(same),
            'declined': len(declined),
            'declined_or_same': len(declined_or_same),
        },
        'percentages': {
            'improved': improved_pct,
            'same': same_pct,
            'declined': declined_pct,
            'declined_or_same': declined_or_same_pct,
        },
        'avg_improvement': avg_improvement,
        'avg_decline': avg_decline,
        'suggestions': suggestions,
    }

def correlate_attendance_and_grades(students: List[Dict[str, Any]], threshold: float = 80.0) -> Dict[str, Any]:
    low_attendance = [
        s for s in students
        if s.get('attendance_percent') is not None and s['attendance_percent'] < threshold
    ]
    high_attendance = [
        s for s in students
        if s.get('attendance_percent') is not None and s['attendance_percent'] >= threshold
    ]
    if not low_attendance and not high_attendance:
        return {
            'threshold': threshold,
            'low_count': 0,
            'high_count': 0,
            'low_avg_grade': 0.0,
            'high_avg_grade': 0.0,
            'grade_difference': 0.0,
            'insights': [],
            'suggestions': [],
        }
    low_avg_grade = 0.0
    high_avg_grade = 0.0
    if low_attendance:
        low_grades = [s.get('weighted_grade', 0) for s in low_attendance if s.get('weighted_grade') is not None]
        low_avg_grade = sum(low_grades) / len(low_grades) if low_grades else 0.0
    if high_attendance:
        high_grades = [s.get('weighted_grade', 0) for s in high_attendance if s.get('weighted_grade') is not None]
        high_avg_grade = sum(high_grades) / len(high_grades) if high_grades else 0.0
    insights: List[str] = []
    suggestions: List[str] = []
    if low_attendance and high_attendance:
        qualifier = "significantly worse" if low_avg_grade < high_avg_grade else "similarly"
        insights.append(
            f"Low-attendance students (avg {low_avg_grade:.1f}%) performed {qualifier} vs high-attendance students (avg {high_avg_grade:.1f}%)."
        )
        grade_difference = high_avg_grade - low_avg_grade
        if grade_difference > 10:
            suggestions.append("Strong correlation: encourage better attendance (large grade gap).")
        elif grade_difference > 5:
            suggestions.append("Moderate correlation between attendance and grades.")
        else:
            insights.append("Correlation appears weak (small grade gap).")
    elif low_attendance:
        insights.append(f"Low-attendance group avg grade: {low_avg_grade:.1f}%.")
        suggestions.append("All students have low attendance—focus on improving attendance rates.")
    else:
        insights.append(f"High-attendance group avg grade: {high_avg_grade:.1f}%.")
        insights.append(f"All students meet attendance threshold (≥{threshold:.0f}%).")
    return {
        'threshold': threshold,
        'low_count': len(low_attendance),
        'high_count': len(high_attendance),
        'low_avg_grade': low_avg_grade,
        'high_avg_grade': high_avg_grade,
        'grade_difference': high_avg_grade - low_avg_grade,
        'insights': insights,
        'suggestions': suggestions,
    }

def get_at_risk_students(students: List[Dict[str, Any]], cutoff: float) -> List[Dict[str, Any]]:
    """Return students whose weighted_grade is below the given cutoff."""
    at_risk: List[Dict[str, Any]] = []
    try:
        cutoff_value = float(cutoff)
    except (TypeError, ValueError):
        return at_risk
    for student in students:
        grade = student.get("weighted_grade")
        if grade is None:
            continue
        try:
            grade_value = float(grade)
        except (TypeError, ValueError):
            continue
        if grade_value < cutoff_value:
            at_risk.append(student)
    return at_risk

def compare_sections(sections_data: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    average_scores: Dict[str, Dict[str, float]] = {}
    all_quiz_keys: List[str] = []
    for students in sections_data.values():
        if students:
            for key in students[0].keys():
                if key.startswith('quiz') and key not in all_quiz_keys:
                    all_quiz_keys.append(key)
    sorted_quiz_keys = sorted(all_quiz_keys)
    for section_name, students in sections_data.items():
        section_averages: Dict[str, float] = {}
        for quiz_key in sorted_quiz_keys:
            scores = [student.get(quiz_key) for student in students if student.get(quiz_key) is not None]
            section_averages[quiz_key] = (sum(scores) / len(scores)) if scores else 0.0
        average_scores[section_name] = section_averages
    insights: List[str] = []
    lowest_per_quiz: Dict[str, Dict[str, Any]] = {}
    if len(sections_data) > 1:
        for quiz_key in sorted_quiz_keys:
            lowest_section = min(average_scores, key=lambda s: average_scores[s][quiz_key]) if average_scores else ""
            lowest_avg = average_scores[lowest_section][quiz_key] if lowest_section else 0.0
            lowest_per_quiz[quiz_key] = {"section": lowest_section, "avg": lowest_avg}
            comparison_parts = [
                f"{section}: {average_scores[section][quiz_key]:.0f}%"
                for section in sorted(average_scores.keys())
            ]
            insight_str = ", ".join(comparison_parts)
            pretty_quiz = quiz_key.replace('_', ' ').title()
            insights.append(f"{pretty_quiz} — {insight_str}.")
            insights.append(f"Lowest average for {pretty_quiz}: {lowest_section} ({lowest_avg:.0f}%).")
    return {
        'average_scores': average_scores,
        'quiz_keys': sorted_quiz_keys,
        'lowest_per_quiz': lowest_per_quiz,
        'insights': insights,
    }

def find_hardest_topic(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    quiz_averages, quiz_counts, hardest, lowest = get_quiz_averages(students)
    if not quiz_averages:
        return {
            'quiz_averages': {},
            'quiz_counts': {},
            'hardest_quiz': "",
            'lowest_avg': 0.0,
            'insight': "",
            'suggestion': "",
        }
    if not hardest:
        return {
            'quiz_averages': quiz_averages,
            'quiz_counts': quiz_counts,
            'hardest_quiz': "",
            'lowest_avg': 0.0,
            'insight': "",
            'suggestion': "",
        }
    pretty = hardest.replace('_', ' ').title()
    insight = f"The lowest-scoring activity was {pretty} ({lowest:.1f}%)."
    suggestion = f"The topic for {pretty} appears to be a class-wide weakness; review recommended."
    return {
        'quiz_averages': quiz_averages,
        'quiz_counts': quiz_counts,
        'hardest_quiz': hardest,
        'lowest_avg': lowest,
        'insight': insight,
        'suggestion': suggestion,
    }


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


def get_attendance_grade_correlation(students: List[Dict[str, Any]], threshold: float = 80.0) -> Dict[str, Any]:
    low_attendance = [
        s for s in students
        if s.get('attendance_percent') is not None and s['attendance_percent'] < threshold
    ]
    high_attendance = [
        s for s in students
        if s.get('attendance_percent') is not None and s['attendance_percent'] >= threshold
    ]
    
    low_avg_grade = 0.0
    high_avg_grade = 0.0
    
    if low_attendance:
        low_grades = [s.get('weighted_grade', 0) for s in low_attendance if s.get('weighted_grade') is not None]
        low_avg_grade = sum(low_grades) / len(low_grades) if low_grades else 0.0
    
    if high_attendance:
        high_grades = [s.get('weighted_grade', 0) for s in high_attendance if s.get('weighted_grade') is not None]
        high_avg_grade = sum(high_grades) / len(high_grades) if high_grades else 0.0
    
    return {
        'threshold': threshold,
        'low_count': len(low_attendance),
        'high_count': len(high_attendance),
        'low_avg_grade': low_avg_grade,
        'high_avg_grade': high_avg_grade,
        'grade_difference': high_avg_grade - low_avg_grade
    }