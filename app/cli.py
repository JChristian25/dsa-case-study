from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from time import sleep
import sys
import readchar
import csv
import os
from typing import Any, Dict, List, Optional, Tuple, Callable

from app.core import (
    load_config,
    read_csv_data,
    group_students_by_section,
    insert_student as core_insert_student,
    delete_student as core_delete_student,
    sort_students,
)
from app.analytics.stats import (
    compute_weighted_grades,
    calculate_distribution,
    get_top_n_students,
    get_bottom_n_students,
    get_average_grade,
    apply_grade_curve as stats_apply_curve,
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

console = Console()

# =====================================
# Helpers and State
# =====================================
def prompt_int(prompt_text: str, default: int, min_value: Optional[int] = None, max_value: Optional[int] = None) -> int:
    try:
        raw = input(f"{prompt_text} ").strip()
        if raw == "":
            return default
        value = int(raw)
        if min_value is not None and value < min_value:
            return default
        if max_value is not None and value > max_value:
            return default
        return value
    except Exception:
        return default

def prompt_float(prompt_text: str, default: float, min_value: Optional[float] = None, max_value: Optional[float] = None) -> float:
    try:
        raw = input(f"{prompt_text} ").strip()
        if raw == "":
            return default
        value = float(raw)
        if min_value is not None and value < min_value:
            return default
        if max_value is not None and value > max_value:
            return default
        return value
    except Exception:
        return default

def prompt_str(prompt_text: str, default: Optional[str] = None) -> str:
    raw = input(f"{prompt_text} ").strip()
    if raw == "" and default is not None:
        return default
    return raw

def _paginate_loop(render_page_fn: Callable[[int, int, int], None], total_items: int, page_size: int = 10) -> None:
    if total_items <= 0:
        console.print("[bold red]No data to display.[/bold red]")
        input("Press Enter to return...")
        return
    index = 0
    max_index = (total_items - 1) // page_size * page_size
    while True:
        render_page_fn(index, min(index + page_size, total_items), total_items)
        console.print("[dim]Use ←/→ to navigate pages. Press q / Esc / Backspace to return.[/dim]")
        key = readchar.readkey()
        if key == readchar.key.RIGHT:
            index = 0 if index >= max_index else index + page_size
        elif key == readchar.key.LEFT:
            index = max_index if index == 0 else index - page_size
        elif key in (readchar.key.ESC, readchar.key.BACKSPACE, "q", "Q"):
            break

def paginate_students_table(students: List[Dict[str, Any]], base_title: str, page_size: int = 10) -> None:
    total = len(students)
    def render(i_start: int, i_end: int, total_items: int) -> None:
        console.clear()
        title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
        console.print(build_student_table(students[i_start:i_end], title=title))
    _paginate_loop(render, total, page_size)

def paginate_rank_table(rows: List[Dict[str, Any]], base_title: str, page_size: int = 10) -> None:
    total = len(rows)
    def render(i_start: int, i_end: int, total_items: int) -> None:
        console.clear()
        title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
        console.print(build_rank_table(rows[i_start:i_end], title=title))
    _paginate_loop(render, total, page_size)

def paginate_section_summary(sections_map: Dict[str, List[Dict[str, Any]]], averages: Dict[str, float], base_title: str, page_size: int = 10) -> None:
    section_names = sorted(sections_map.keys())
    total = len(section_names)
    if total == 0:
        console.print("[bold red]No sections available.[/bold red]")
        input("Press Enter to return...")
        return
    def render(i_start: int, i_end: int, total_items: int) -> None:
        console.clear()
        subset_names = section_names[i_start:i_end]
        subset_map = {sec: sections_map[sec] for sec in subset_names}
        title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
        console.print(build_section_summary_table(subset_map, averages, title=title))
    _paginate_loop(render, total, page_size)

def load_or_reload_data(config_path: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    console.clear()
    console.print("[bold yellow]Loading configuration and data...[/bold yellow]")
    chosen_path = config_path or prompt_str("Config path (default 'config.json'):", "config.json")
    config = load_config(chosen_path)
    students_raw = read_csv_data(config["file_paths"]["input_csv"])
    students = compute_weighted_grades(students_raw, config["grade_weights"])
    sections = group_students_by_section(students)
    console.print("[bold green]Data loaded.[/bold green]")
    input("Press Enter to continue...")
    return students, sections, chosen_path

def insert_demo_student(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    config = load_config(config_path)
    new_student: Dict[str, Any] = {
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
    core_insert_student(sections, new_student)
    students.append(new_student)
    console.print(f"[bold green]Inserted {new_student['first_name']} {new_student['last_name']} into {new_student['section']}[/bold green]")
    input("Press Enter to continue...")
    return students, sections

def delete_student_by_id(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    student_id = prompt_str("Enter Student ID to delete:", "")
    if not student_id:
        return students, sections
    if core_delete_student(sections, student_id):
        students = [s for s in students if s.get("student_id") != student_id]
        console.print(f"[bold green]Deleted student with ID {student_id}[/bold green]")
    else:
        console.print(f"[bold red]No student found with ID {student_id}[/bold red]")
    input("Press Enter to continue...")
    return students, sections

# =====================================
# Animated Title (might change)
# =====================================
def animated_title() -> None:
    title_text = "📊 Academic Analytics Lite 📊"
    bg_style = "on #0f1a26"
    colors = ["cyan", "magenta", "yellow", "green", "blue"]

    for i in range(1, len(title_text)+1):
        console.clear()
        console.print(Panel(title_text[:i], style=f"bold cyan {bg_style}", expand=False, border_style="bright_cyan"))
        sleep(0.05)

    for _ in range(2):
        for color in colors:
            console.clear()
            console.print(Panel(title_text, style=f"bold {color} {bg_style}", expand=False, border_style=color))
            sleep(0.4)
  
    console.clear()
    console.print(Panel(title_text, style=f"bold cyan {bg_style}", expand=False, border_style="cyan"))
    sleep(0.8)

# =====================================
# Arrow-key menu navigation with levels
# =====================================
def arrow_menu(title: str, options: Dict[str, str], level: int = 1) -> str:
    keys = list(options.keys())
    selected = 0
    if level == 1:
        panel_style = "bold cyan on #0f1a26"
        border_color = "cyan"
    elif level == 2:
        panel_style = "bold #008b8b on #0f1a26"  # teal/dark cyan
        border_color = "#008b8b"
    else:
        panel_style = "bold #005757 on #0f1a26"  # darker cyan for third-level
        border_color = "#005757"

    while True:
        console.clear()
        console.print(Panel(f"📂 {title}", style=panel_style, expand=False, border_style=border_color))
        table = Table(title="Select an Option", style=panel_style)
        table.add_column("Option", justify="center")
        table.add_column("Description", justify="left")
        for i, (key, desc) in enumerate(options.items()):
            if i == selected:
                table.add_row(f"> {key} <", f"[bold green]{desc}[/bold green]")
            else:
                table.add_row(f"  {key}  ", desc)
        console.print(table)
        console.print("[dim]Use ↑ ↓ to navigate and Enter to select.[/dim]")

        key = readchar.readkey()
        if key == readchar.key.UP:
            selected = (selected - 1) % len(keys)
        elif key == readchar.key.DOWN:
            selected = (selected + 1) % len(keys)
        elif key == readchar.key.ENTER:
            return keys[selected]

# =====================================
# Renderers (Showcase-integrated)
# =====================================
def view_overall_roster(students: List[Dict[str, Any]]) -> None:
    console.clear()
    paginate_students_table(students, base_title="Overall Roster", page_size=10)

def view_overall_distribution(students: List[Dict[str, Any]], config_path: str) -> None:
    console.clear()
    cfg = load_config(config_path)
    dist = calculate_distribution(students, cfg["thresholds"]["grade_letters"])
    console.print(build_distribution_table(dist, total=len(students), title="Overall Grade Distribution"))
    input("Press Enter to return...")

def view_section_summary(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    averages = {sec: get_average_grade(studs) for sec, studs in sections.items()}
    paginate_section_summary(sections, averages, base_title="Average Grade per Section", page_size=10)

def view_overall_ranking(students: List[Dict[str, Any]]) -> None:
    console.clear()
    n = prompt_int("Top N (default 10):", 10, 1, 1000)
    top_students = get_top_n_students(students, n)
    rows = [dict(rank=i + 1, **s) for i, s in enumerate(top_students)]
    paginate_rank_table(rows, base_title=f"Top {n} — Overall", page_size=10)

def view_curve_preview(students: List[Dict[str, Any]]) -> None:
    console.clear()
    method = prompt_str("Curve method [flat|normalize] (default flat):", "flat")
    if method == "normalize":
        target_max = prompt_int("Target max grade (default 100):", 100, 1, 100)
        curved = stats_apply_curve([s.copy() for s in students], method="normalize", value=float(target_max))
    else:
        points = prompt_float("Flat curve points to add (default 5):", 5.0, -100.0, 100.0)
        curved = stats_apply_curve([s.copy() for s in students], method="flat", value=float(points))
    preview = prompt_int("Preview how many students? (default 5):", 5, 1, len(curved))
    console.print(build_curve_table(curved[:preview], title="Curve Preview"))
    input("Press Enter to return...")

def _select_section(sections: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
    if not sections:
        console.print("[bold red]No sections available.[/bold red]")
        input("Press Enter to return...")
        return None
    options = {str(i + 1): sec for i, sec in enumerate(sorted(sections.keys()))}
    options[str(len(options) + 1)] = "Back"
    choice = arrow_menu("Select Section", options, level=3)
    if choice == str(len(options)):
        return None
    return options.get(choice)

def view_section_table(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    paginate_students_table(sections.get(section, []), base_title=f"Section: {section}", page_size=10)

def sort_section_menu(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    sort_opts = {"1": "weighted_grade (desc)", "2": "last_name", "3": "first_name", "4": "Back"}
    choice = arrow_menu(f"Sort {section}", sort_opts, level=3)
    if choice == "4":
        return
    if choice == "1":
        sorted_list = sort_students(studs, sort_by="weighted_grade", reverse=True)
        title = f"Sorted by Grade (desc) — {section}"
    elif choice == "2":
        sorted_list = sort_students(studs, sort_by="last_name")
        title = f"Sorted by Last Name — {section}"
    else:
        sorted_list = sort_students(studs, sort_by="first_name")
        title = f"Sorted by First Name — {section}"
    paginate_students_table(sorted_list, base_title=title, page_size=10)

def section_top_bottom_menu(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    n = prompt_int("N (default 3):", 3, 1, len(studs) if studs else 1)
    opts = {"1": "Top N", "2": "Bottom N", "3": "Back"}
    choice = arrow_menu(f"Top/Bottom — {section}", opts, level=3)
    if choice == "3":
        return
    if choice == "1":
        selected = get_top_n_students(studs, n)
        title = f"Top {n} — {section}"
    else:
        selected = get_bottom_n_students(studs, n)
        title = f"Bottom {n} — {section}"
    rows = [dict(rank=i + 1, **s) for i, s in enumerate(selected)]
    paginate_rank_table(rows, base_title=title, page_size=10)

def section_distribution(sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    cfg = load_config(config_path)
    dist = calculate_distribution(studs, cfg["thresholds"]["grade_letters"])
    console.print(build_distribution_table(dist, total=len(studs), title=f"Grade Distribution — {section}"))
    input("Press Enter to return...")

def section_hardest_topic(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    quiz_avgs, quiz_counts, hardest_quiz, lowest = get_quiz_averages(studs)
    console.print(build_hardest_topic_table(quiz_avgs, quiz_counts, hardest_quiz, title=f"Hardest Topic — {section}"))
    input("Press Enter to return...")

def view_quiz_comparison(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    avg_by_section, quiz_keys, lowest_per_quiz = get_sections_quiz_averages(sections)
    console.print(build_quiz_comparison_table(avg_by_section, quiz_keys, lowest_per_quiz, title="Quiz Averages Comparison"))
    input("Press Enter to return...")

# =====================================
# Lookup Student Submenu
# =====================================
def lookup_student(students: List[Dict[str, Any]]) -> None:
    options = {
        "1": "By ID",
        "2": "By First Name",
        "3": "By Middle Name",
        "4": "By Last Name",
        "5": "Back"
    }
    while True:
        choice = arrow_menu("Lookup Individual Student", options, level=3)
        if choice == "5":
            break
        elif choice == "1":
            lookup_by_id(students)
        elif choice == "2":
            lookup_by_first_name(students)
        elif choice == "3":
            lookup_by_middle_name(students)
        elif choice == "4":
            lookup_by_last_name(students)

def lookup_by_id(students: List[Dict[str, Any]]) -> None:
    console.clear()
    student_id = input("Enter Student ID: ").strip()
    results = [s for s in students if str(s.get("student_id","")).lower() == student_id.lower()]
    if results:
        paginate_students_table(results, base_title=f"Results: ID {student_id}", page_size=10)
    else:
        console.print(f"[bold red]No student found with ID {student_id}[/bold red]")
    input("Press Enter to return to Lookup Menu...")

def lookup_by_first_name(students: List[Dict[str, Any]]) -> None:
    console.clear()
    first_name = input("Enter First Name: ").strip()
    results = [s for s in students if str(s.get("first_name","")).lower() == first_name.lower()]
    if results:
        paginate_students_table(results, base_title=f"Results: First Name '{first_name}'", page_size=10)
    else:
        console.print(f"[bold red]No results for first name '{first_name}'[/bold red]")
    input("Press Enter to return to Lookup Menu...")

def lookup_by_middle_name(students: List[Dict[str, Any]]) -> None:
    console.clear()
    middle_name = input("Enter Middle Name: ").strip()
    results = [s for s in students if str(s.get("middle_name","")).lower() == middle_name.lower()]
    if results:
        paginate_students_table(results, base_title=f"Results: Middle Name '{middle_name}'", page_size=10)
    else:
        console.print(f"[bold red]No results for middle name '{middle_name}'[/bold red]")
    input("Press Enter to return to Lookup Menu...")

def lookup_by_last_name(students: List[Dict[str, Any]]) -> None:
    console.clear()
    last_name = input("Enter Last Name: ").strip()
    results = [s for s in students if str(s.get("last_name","")).lower() == last_name.lower()]
    if results:
        paginate_students_table(results, base_title=f"Results: Last Name '{last_name}'", page_size=10)
    else:
        console.print(f"[bold red]No results for last name '{last_name}'[/bold red]")
    input("Press Enter to return to Lookup Menu...")

# =====================================
# Submenus
# =====================================
def course_dashboard(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "1.a": "View Overall Roster",
        "1.b": "View Overall Grade Distribution",
        "1.c": "View Section Averages",
        "1.d": "View Overall Ranking (Top N)",
        "1.e": "Curve Preview",
        "1.f": "Back"
    }
    while True:
        choice = arrow_menu("Course Dashboard", options, level=2)
        if choice == "1.f":
            break
        elif choice == "1.a":
            view_overall_roster(students)
        elif choice == "1.b":
            view_overall_distribution(students, config_path)
        elif choice == "1.c":
            view_section_summary(sections)
        elif choice == "1.d":
            view_overall_ranking(students)
        elif choice == "1.e":
            view_curve_preview(students)
    return students, sections, config_path

def section_analytics(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "2.a": "View Section Table",
        "2.b": "Sort a Section",
        "2.c": "Top/Bottom N in Section",
        "2.d": "Section Grade Distribution",
        "2.e": "Hardest Topic per Section",
        "2.f": "Quiz Averages Comparison (All Sections)",
        "2.g": "Back"
    }
    while True:
        choice = arrow_menu("Section Analytics", options, level=2)
        if choice == "2.g":
            break
        elif choice == "2.a":
            view_section_table(sections)
        elif choice == "2.b":
            sort_section_menu(sections)
        elif choice == "2.c":
            section_top_bottom_menu(sections)
        elif choice == "2.d":
            section_distribution(sections, config_path)
        elif choice == "2.e":
            section_hardest_topic(sections)
        elif choice == "2.f":
            view_quiz_comparison(sections)
    return students, sections, config_path

def student_reports(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "3.a": "View 'At-Risk' Student List",
        "3.b": "Export Section Reports to CSV",
        "3.c": "Look Up Individual Student",
        "3.d": "Back"
    }
    while True:
        choice = arrow_menu("Student Reports", options, level=2)
        if choice == "3.d":
            break
        elif choice == "3.a":
            cfg = load_config(config_path)
            cutoff = cfg["thresholds"]["at_risk_cutoff"]
            at_risk = [s for s in students if isinstance(s.get("weighted_grade"), (int, float)) and s["weighted_grade"] < float(cutoff)]
            paginate_students_table(at_risk, base_title=f"At-Risk Students (cutoff {cutoff})", page_size=10)
        elif choice == "3.b":
            cfg = load_config(config_path)
            out_dir = cfg["file_paths"]["output_dir"]
            os.makedirs(out_dir, exist_ok=True)
            for section_name, section_data in sections.items():
                if section_data:
                    export_to_csv(section_data, os.path.join(out_dir, f"section_{section_name}_report.csv"))
            console.print("[bold green]Section reports exported.[/bold green]")
            input("Press Enter to return...")
        elif choice == "3.c":
            lookup_student(students)
    return students, sections, config_path

def tools_utilities(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "4.a": "Load/Reload Data",
        "4.b": "Insert Demo Student",
        "4.c": "Delete Student by ID",
        "4.d": "Back"
    }
    while True:
        choice = arrow_menu("Tools & Utilities", options, level=2)
        if choice == "4.d":
            break
        elif choice == "4.a":
            students, sections, config_path = load_or_reload_data(config_path)
        elif choice == "4.b":
            if not students:
                console.print("[bold red]Load data first.[/bold red]")
                input("Press Enter to continue...")
            else:
                students, sections = insert_demo_student(students, sections, config_path)
        elif choice == "4.c":
            if not students:
                console.print("[bold red]Load data first.[/bold red]")
                input("Press Enter to continue...")
            else:
                students, sections = delete_student_by_id(students, sections)
    return students, sections, config_path

# =====================================
# Main Menu
# =====================================
def run_menu() -> None:
    animated_title()
    options = {"1": "Course Dashboard", "2": "Section Analytics",
               "3": "Student Reports", "4": "Tools & Utilities", "5": "Exit"}
    students: List[Dict[str, Any]] = []
    sections: Dict[str, List[Dict[str, Any]]] = {}
    config_path: str = "config.json"
    students, sections, config_path = load_or_reload_data(config_path)
    while True:
        choice = arrow_menu("Main Menu", options, level=1)
        if choice == "1":
            students, sections, config_path = course_dashboard(students, sections, config_path)
        elif choice == "2":
            students, sections, config_path = section_analytics(students, sections, config_path)
        elif choice == "3":
            students, sections, config_path = student_reports(students, sections, config_path)
        elif choice == "4":
            students, sections, config_path = tools_utilities(students, sections, config_path)
        elif choice == "5":
            console.clear()
            console.print("[bold green]Exiting program. Goodbye![/bold green]")
            sys.exit()

# =====================================
# Main Execution
# =====================================
if __name__ == "__main__":
    run_menu()
