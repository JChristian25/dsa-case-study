from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.align import Align
from rich.text import Text
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
from app.reporting.plotting import (
    plot_grade_histogram,
    plot_combined_histogram,
    _is_display_available,
)

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
    from rich.align import Align
    from rich.text import Text
    
    console.clear()
    
    # Loading header
    header = Panel(
        Align.center(Text("📂 DATA LOADING", style="bold cyan")),
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(Align.center(header))
    console.print()
    
    chosen_path = config_path or prompt_str("Config path (default 'config.json'):", "config.json")
    
    # Progress animation
    with Progress(console=console) as progress:
        task1 = progress.add_task("[cyan]Loading configuration...", total=100)
        for _ in range(100):
            progress.update(task1, advance=1)
            sleep(0.005)
        
        config = load_config(chosen_path)
        console.print("[bold green]✓[/bold green] Configuration loaded")
        
        task2 = progress.add_task("[cyan]Reading CSV data...", total=100)
        for _ in range(100):
            progress.update(task2, advance=1)
            sleep(0.005)
        
        students_raw = read_csv_data(config["file_paths"]["input_csv"], config)
        console.print(f"[bold green]✓[/bold green] Loaded {len(students_raw)} student records")
        
        task3 = progress.add_task("[cyan]Computing weighted grades...", total=100)
        for _ in range(100):
            progress.update(task3, advance=1)
            sleep(0.005)
        
        students = compute_weighted_grades(students_raw, config["grade_weights"])
        console.print("[bold green]✓[/bold green] Grades computed")
        
        task4 = progress.add_task("[cyan]Grouping by sections...", total=100)
        for _ in range(100):
            progress.update(task4, advance=1)
            sleep(0.005)
        
        sections = group_students_by_section(students)
        console.print(f"[bold green]✓[/bold green] Organized into {len(sections)} sections")
    
    console.print()
    success_panel = Panel(
        Align.center(Text("✨ DATA LOADED SUCCESSFULLY ✨", style="bold green")),
        border_style="green",
        padding=(1, 2)
    )
    console.print(Align.center(success_panel))
    
    input("\nPress Enter to continue...")
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
    from rich.align import Align
    from rich.text import Text
    import platform
    
    console.clear()
    
    # ASCII Art Title
    title_art = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║      █████╗  ██████╗ █████╗ ██████╗ ███████╗███╗   ███╗██╗   ║
    ║     ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗ ████║██║   ║
    ║     ███████║██║     ███████║██║  ██║█████╗  ██╔████╔██║██║   ║
    ║     ██╔══██║██║     ██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║   ║
    ║     ██║  ██║╚██████╗██║  ██║██████╔╝███████╗██║ ╚═╝ ██║██║   ║
    ║     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝   ║
    ║                                                               ║
    ║          📊  A C A D E M I C   A N A L Y T I C S  📊          ║
    ║                         L I T E                               ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    
    # Gradient color animation
    colors = ["cyan", "bright_cyan", "blue", "bright_blue", "magenta", "bright_magenta"]
    
    for color in colors:
        console.clear()
        styled_title = Text(title_art, style=f"bold {color}")
        console.print(Align.center(styled_title))
        sleep(0.15)
    
    # Final display with info
    console.clear()
    final_title = Text(title_art, style="bold cyan")
    console.print(Align.center(final_title))
    
    # System info panel
    info_text = Text()
    info_text.append("System: ", style="bold yellow")
    info_text.append(f"{platform.system()} {platform.release()}\n", style="white")
    info_text.append("Python: ", style="bold yellow")
    info_text.append(f"{platform.python_version()}\n", style="white")
    info_text.append("Status: ", style="bold yellow")
    info_text.append("Ready", style="bold green")
    
    info_panel = Panel(
        Align.center(info_text),
        title="[bold white]System Information[/bold white]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(Align.center(info_panel))
    console.print()
    
    # Progress bar animation
    with Progress(console=console) as progress:
        task = progress.add_task("[cyan]Initializing...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            sleep(0.01)
    
    console.print()
    console.print(Align.center("[bold green]✓ System Ready[/bold green]"))
    sleep(0.8)
    console.clear()

# =====================================
# Arrow-key menu navigation with levels
# =====================================
def arrow_menu(title: str, options: Dict[str, str], level: int = 1) -> str:
    from rich.align import Align
    
    keys = list(options.keys())
    selected = 0
    if level == 1:
        panel_style = "bold cyan on #0f1a26"
        border_color = "cyan"
        icon = "🏠"
    elif level == 2:
        panel_style = "bold #008b8b on #0f1a26"  # teal/dark cyan
        border_color = "#008b8b"
        icon = "📂"
    else:
        panel_style = "bold #005757 on #0f1a26"  # darker cyan for third-level
        border_color = "#005757"
        icon = "📄"

    while True:
        console.clear()
        
        # Enhanced title panel
        title_panel = Panel(
            Align.center(f"{icon}  {title}  {icon}"),
            style=panel_style,
            border_style=border_color,
            padding=(1, 4)
        )
        console.print(Align.center(title_panel))
        console.print()
        
        # Options table
        table = Table(
            title="[bold cyan]Select an Option[/bold cyan]",
            style=panel_style,
            show_header=True,
            header_style="bold yellow",
            border_style=border_color,
            expand=False
        )
        table.add_column("Key", justify="center", style="bold white", width=8)
        table.add_column("Option", justify="left", width=40)
        
        for i, (key, desc) in enumerate(options.items()):
            if i == selected:
                table.add_row(
                    f"▶ {key} ◀",
                    f"[bold green]{desc}[/bold green]",
                    style="on #1a3a3a"
                )
            else:
                table.add_row(f"  {key}  ", desc)
        
        console.print(Align.center(table))
        console.print()
        
        # Instructions
        instructions = Panel(
            "[dim]Use [bold]↑ ↓[/bold] to navigate  •  Press [bold]Enter[/bold] to select[/dim]",
            border_style="dim",
            padding=(0, 2)
        )
        console.print(Align.center(instructions))

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
# Plotting Functions
# =====================================
def plot_overall_histograms(students: List[Dict[str, Any]]) -> None:
    console.clear()
    console.print("[bold cyan]Select histogram type:[/bold cyan]")
    options = {
        "1": "Weighted Grade Distribution",
        "2": "Quiz Scores Distribution",
        "3": "Midterm vs Final",
        "4": "Attendance Distribution",
        "5": "All Scores Combined",
        "6": "Generate All Plots",
        "7": "Back"
    }
    choice = arrow_menu("Overall Histograms", options, level=3)
    
    has_display = _is_display_available()
    display_msg = " (and displayed)" if has_display else ""
    
    if choice == "1":
        file_path = plot_grade_histogram(students, "weighted_grade", "Overall Weighted Grade Distribution")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "2":
        file_path = plot_combined_histogram(students, ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5"], "Quiz Scores Distribution")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "3":
        file_path = plot_combined_histogram(students, ["midterm", "final"], "Midterm vs Final Exam Distribution")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "4":
        file_path = plot_grade_histogram(students, "attendance_percent", "Attendance Distribution")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "5":
        file_path = plot_combined_histogram(
            students,
            ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade"],
            "All Scores including Weighted Grade"
        )
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "6":
        console.print("[bold yellow]Generating all plots...[/bold yellow]")
        f1 = plot_grade_histogram(students, "weighted_grade", "Overall Weighted Grade Distribution")
        f2 = plot_combined_histogram(students, ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5"], "Quiz Scores Distribution")
        f3 = plot_combined_histogram(students, ["midterm", "final"], "Midterm vs Final Exam Distribution")
        f4 = plot_grade_histogram(students, "attendance_percent", "Attendance Distribution")
        f5 = plot_combined_histogram(
            students,
            ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade"],
            "All Scores including Weighted Grade"
        )
        if has_display:
            console.print(f"[bold green]All plots saved to output/plots/ and displayed![/bold green]")
        else:
            console.print(f"[bold green]All plots saved to output/plots/ (check folder to view)[/bold green]")
        input("Press Enter to continue...")

def plot_section_histograms(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    
    studs = sections[section]
    console.print(f"[bold cyan]Select histogram for {section}:[/bold cyan]")
    options = {
        "1": "Weighted Grade Distribution",
        "2": "Quiz Scores Distribution",
        "3": "Midterm vs Final",
        "4": "Attendance Distribution",
        "5": "All Scores Combined",
        "6": "Generate All Plots",
        "7": "Back"
    }
    choice = arrow_menu(f"Section Histograms - {section}", options, level=3)
    
    has_display = _is_display_available()
    display_msg = " (and displayed)" if has_display else ""
    
    if choice == "1":
        file_path = plot_grade_histogram(studs, "weighted_grade", f"Weighted Grade Distribution - {section}")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "2":
        file_path = plot_combined_histogram(studs, ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5"], f"Quiz Scores Distribution - {section}")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "3":
        file_path = plot_combined_histogram(studs, ["midterm", "final"], f"Midterm vs Final - {section}")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "4":
        file_path = plot_grade_histogram(studs, "attendance_percent", f"Attendance Distribution - {section}")
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "5":
        file_path = plot_combined_histogram(
            studs,
            ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade"],
            f"All Scores - {section}"
        )
        console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
        input("Press Enter to continue...")
    elif choice == "6":
        console.print("[bold yellow]Generating all plots...[/bold yellow]")
        plot_grade_histogram(studs, "weighted_grade", f"Weighted Grade Distribution - {section}")
        plot_combined_histogram(studs, ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5"], f"Quiz Scores Distribution - {section}")
        plot_combined_histogram(studs, ["midterm", "final"], f"Midterm vs Final - {section}")
        plot_grade_histogram(studs, "attendance_percent", f"Attendance Distribution - {section}")
        plot_combined_histogram(
            studs,
            ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade"],
            f"All Scores - {section}"
        )
        if has_display:
            console.print(f"[bold green]All plots saved to output/plots/ and displayed![/bold green]")
        else:
            console.print(f"[bold green]All plots saved to output/plots/ (check folder to view)[/bold green]")
        input("Press Enter to continue...")

def plot_custom_histogram(students: List[Dict[str, Any]]) -> None:
    console.clear()
    console.print("[bold cyan]Select column to plot:[/bold cyan]")
    console.print("Available: quiz1, quiz2, quiz3, quiz4, quiz5, midterm, final, weighted_grade, attendance_percent")
    key = prompt_str("Enter column name:", "weighted_grade")
    
    if key not in ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade", "attendance_percent"]:
        console.print(f"[bold red]Invalid column: {key}[/bold red]")
        input("Press Enter to continue...")
        return
    
    has_display = _is_display_available()
    display_msg = " (and displayed)" if has_display else ""
    
    file_path = plot_grade_histogram(students, key)
    console.print(f"[bold green]Plot saved to: {file_path}{display_msg}[/bold green]")
    input("Press Enter to continue...")

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
        "1.f": "Overall Histograms",
        "1.g": "Back"
    }
    while True:
        choice = arrow_menu("Course Dashboard", options, level=2)
        if choice == "1.g":
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
        elif choice == "1.f":
            plot_overall_histograms(students)
    return students, sections, config_path

def section_analytics(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "2.a": "View Section Table",
        "2.b": "Sort a Section",
        "2.c": "Top/Bottom N in Section",
        "2.d": "Section Grade Distribution",
        "2.e": "Hardest Topic per Section",
        "2.f": "Quiz Averages Comparison (All Sections)",
        "2.g": "Section Histograms",
        "2.h": "Back"
    }
    while True:
        choice = arrow_menu("Section Analytics", options, level=2)
        if choice == "2.h":
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
        elif choice == "2.g":
            plot_section_histograms(sections)
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
        "4.d": "Custom Histogram Plot",
        "4.e": "Back"
    }
    while True:
        choice = arrow_menu("Tools & Utilities", options, level=2)
        if choice == "4.e":
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
        elif choice == "4.d":
            if not students:
                console.print("[bold red]Load data first.[/bold red]")
                input("Press Enter to continue...")
            else:
                plot_custom_histogram(students)
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
            
            # Goodbye animation
            goodbye_art = """
            ╔═══════════════════════════════════════════════╗
            ║                                               ║
            ║      _____ _                 _                ║
            ║     |_   _| |__   __ _ _ __ | | _____         ║
            ║       | | | '_ \\ / _` | '_ \\| |/ / __|        ║
            ║       | | | | | | (_| | | | |   <\\__ \\        ║
            ║       |_| |_| |_|\\__,_|_| |_|_|\\_\\___/        ║
            ║                                               ║
            ║           for using Academic Analytics!       ║
            ║                                               ║
            ║                  👋 Goodbye! 👋                ║
            ║                                               ║
            ╚═══════════════════════════════════════════════╝
            """
            
            colors = ["green", "cyan", "blue", "magenta"]
            for color in colors:
                console.clear()
                styled = Text(goodbye_art, style=f"bold {color}")
                console.print(Align.center(styled))
                sleep(0.2)
            
            console.clear()
            final_goodbye = Panel(
                Align.center(Text("✨ Session Ended Successfully ✨\n\nThank you for using Academic Analytics Lite!", style="bold green")),
                border_style="green",
                padding=(2, 4)
            )
            console.print("\n" * 3)
            console.print(Align.center(final_goodbye))
            console.print("\n" * 2)
            sleep(1)
            sys.exit()

# =====================================
# Main Execution
# =====================================
if __name__ == "__main__":
    run_menu()
