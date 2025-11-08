from typing import Any, Dict, List
from rich.console import Console

from app.core import (
    load_config,
    read_csv_data,
    group_students_by_section,
    insert_student,
    delete_student,
    sort_students,
)
from app.analytics.stats import (
    compute_weighted_grades,
    calculate_distribution,
    get_top_n_students,
    get_bottom_n_students,
    get_average_grade,
    apply_grade_curve,
)
from app.analytics.insights import (
    get_quiz_averages,
    get_sections_quiz_averages,
)
from app.reporting.tables import (
    build_student_table,
    build_distribution_table,
    build_section_summary_table,
    build_rank_table,
    build_curve_table,
    build_hardest_topic_table,
    build_quiz_comparison_table,
)
from app.reporting.exporter import export_to_csv


def run_showcase(config_path: str = "config.json") -> None:
    console = Console()
    config = load_config(config_path)

    # == INGEST ==
    console.rule("INGEST")
    students = read_csv_data(config["file_paths"]["input_csv"])

    # == TRANSFORM: WEIGHTED GRADES ==
    console.rule("TRANSFORM: WEIGHTED GRADES")
    students = compute_weighted_grades(students, config["grade_weights"])
    console.print(
        build_student_table(
            students,
            title="Overall Roster",
            at_risk_cutoff=config["thresholds"]["at_risk_cutoff"],
        )
    )

    # == GROUP BY SECTION ==
    sections = group_students_by_section(students)

    # == ARRAY OPS: INSERT / DELETE ==
    console.rule("ARRAY OPS: INSERT / DELETE")
    new_student = {
        "student_id": "2024-9999",
        "last_name": "Zzz",
        "first_name": "Alpha",
        "section": "BSIT 2-1",
        "quiz1": 85,
        "quiz2": 90,
        "quiz3": 88,
        "quiz4": 92,
        "quiz5": 89,
        "midterm": 91,
        "final": 93,
        "attendance_percent": 95,
    }
    new_student = compute_weighted_grades([new_student], config["grade_weights"])[0]
    insert_student(sections, new_student)
    students.append(new_student)
    console.print(f"Inserted {new_student['first_name']} {new_student['last_name']} into {new_student['section']}")

    if students:
        to_delete = students[0].get("student_id")
        if delete_student(sections, to_delete):
            students = [s for s in students if s.get("student_id") != to_delete]
            console.print(f"Deleted student with ID {to_delete}")

    # == SECTION TABLES ==
    console.rule("SECTION TABLES")
    for section_name, studs in sections.items():
        section_grades = compute_weighted_grades(studs, config["grade_weights"])
        console.print(
            build_student_table(
                section_grades,
                title=f"Section: {section_name}",
                at_risk_cutoff=config["thresholds"]["at_risk_cutoff"],
            )
        )

    # == SORTING ==
    console.rule("SORTING")
    for section_name, studs in sections.items():
        console.print(
            build_student_table(
                sort_students(studs, sort_by="weighted_grade", reverse=True),
                title=f"Sorted by Grade (desc) — {section_name}",
                at_risk_cutoff=config["thresholds"]["at_risk_cutoff"],
            )
        )
        console.print(
            build_student_table(
                sort_students(studs, sort_by="last_name"),
                title=f"Sorted by Last Name — {section_name}",
                at_risk_cutoff=config["thresholds"]["at_risk_cutoff"],
            )
        )
        console.print(
            build_student_table(
                sort_students(studs, sort_by="first_name"),
                title=f"Sorted by First Name — {section_name}",
                at_risk_cutoff=config["thresholds"]["at_risk_cutoff"],
            )
        )

    # == TOP / BOTTOM N ==
    console.rule("TOP / BOTTOM N")
    N = 3
    for section_name, studs in sections.items():
        top_students = get_top_n_students(studs, N)
        rows = [dict(rank=i + 1, **s) for i, s in enumerate(top_students)]
        console.print(build_rank_table(rows, title=f"Top {N} — {section_name}"))

        bottom_students = get_bottom_n_students(studs, N)
        rows = [dict(rank=i + 1, **s) for i, s in enumerate(bottom_students)]
        console.print(build_rank_table(rows, title=f"Bottom {N} — {section_name}"))

    # == SECTION AVERAGES ==
    console.rule("SECTION AVERAGES")
    averages = {sec: get_average_grade(studs) for sec, studs in sections.items()}
    console.print(
        build_section_summary_table(
            sections, averages, title="Average Grade per Section"
        )
    )

    # == GRADE DISTRIBUTIONS ==
    console.rule("GRADE DISTRIBUTIONS")
    overall_dist = calculate_distribution(students, config["thresholds"]["grade_letters"])
    console.print(
        build_distribution_table(
            overall_dist, total=len(students), title="Overall Grade Distribution"
        )
    )
    for section_name, studs in sections.items():
        dist = calculate_distribution(studs, config["thresholds"]["grade_letters"])
        console.print(
            build_distribution_table(
                dist, total=len(studs), title=f"Grade Distribution — {section_name}"
            )
        )

    # == QUIZ INSIGHTS ==
    console.rule("QUIZ INSIGHTS")
    for section_name, studs in sections.items():
        quiz_avgs, quiz_counts, hardest_quiz, _ = get_quiz_averages(studs)
        console.print(
            build_hardest_topic_table(
                quiz_avgs, quiz_counts, hardest_quiz, title=f"Hardest Topic — {section_name}"
            )
        )
    avg_by_section, quiz_keys, lowest_per_quiz = get_sections_quiz_averages(sections)
    console.print(
        build_quiz_comparison_table(
            avg_by_section, quiz_keys, lowest_per_quiz, title="Quiz Averages Comparison"
        )
    )

    # == CURVING ==
    console.rule("CURVING")
    students = apply_grade_curve(students, method="flat", value=5.0)
    console.print(build_curve_table(students[:5], title="Curve Preview (flat +5)"))
    students = apply_grade_curve(students, method="normalize", value=100.0)
    console.print(build_curve_table(students[:5], title="Curve Preview (normalize to 100)"))

    # == EXPORTS ==
    console.rule("EXPORTS")
    for section_name, section_data in sections.items():
        if section_data:
            export_to_csv(
                section_data,
                f"{config['file_paths']['output_dir']}section_{section_name}_report.csv",
            )

    # == RANKINGS OVERALL == (to add)
    console.rule("RANKINGS OVERALL (to add)")
    console.print("[dim]Overall ranking not yet implemented.[/dim]")

    # == PERCENTILES == (to add)
    console.rule("PERCENTILES (to add)")
    console.print("[dim]Percentile calculations not yet implemented.[/dim]")

    # == OUTLIERS == (to add)
    console.rule("OUTLIERS (to add)")
    console.print("[dim]Outlier detection not yet implemented.[/dim]")

    # == IMPROVEMENT INSIGHTS == (to add)
    console.rule("IMPROVEMENT INSIGHTS (to add)")
    console.print("[dim]Improvement analysis (e.g., midterm→final) not yet implemented.[/dim]")

    # == AT-RISK LIST/EXPORT == (to add)
    console.rule("AT-RISK LIST/EXPORT (to add)")
    console.print("[dim]At-risk list and export not yet implemented.[/dim]")

    # == PLOTS == (to add)
    console.rule("PLOTS (to add)")
    console.print("[dim]Histogram/box plot generation not yet wired in.[/dim]")

    console.rule("DONE")