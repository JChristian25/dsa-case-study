from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from rich.align import Align
from rich.text import Text
from rich.theme import Theme
from rich.layout import Layout
from rich.live import Live
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
    track_midterm_to_final_improvement,
    correlate_attendance_and_grades,
    compare_sections,
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

theme = Theme(
    {
        "app.title": "bold cyan",
        "app.border": "cyan",
        "app.help": "dim",
        "good": "bold green",
        "warn": "yellow",
        "bad": "bold red",
    }
)
console = Console(theme=theme)

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

def _status_text_basic(students: Optional[List[Dict[str, Any]]] = None,
                       sections: Optional[Dict[str, List[Dict[str, Any]]]] = None,
                       config_path: Optional[str] = None) -> str:
    parts: List[str] = []
    if students is not None:
        parts.append(f"Students: {len(students)}")
    if sections is not None:
        parts.append(f"Sections: {len(sections)}")
    if config_path:
        parts.append(f"Config: {config_path}")
    return "  |  ".join(parts)

def _build_layout(header_title: str,
                  help_text: str,
                  status_text: str,
                  *,
                  panel_style: str = "bold cyan on #0f1a26",
                  border_color: str = "cyan") -> Layout:
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )
    header_panel = Panel(
        Align.center(Text(header_title, style="app.title")),
        border_style=border_color,
        style=panel_style,
        padding=(0, 2),
    )
    layout["header"].update(header_panel)
    footer_panel = Panel(
        Align.center(Text.from_markup(f"[app.help]{help_text}[/app.help]\n{status_text or ''}")),
        border_style="dim",
        padding=(0, 2),
    )
    layout["footer"].update(footer_panel)
    return layout

def _show_in_layout(renderable: Any,
                    title: str,
                    help_text: str = "Press Enter or q/Esc/Backspace to return",
                    status_text: str = "",
                    *,
                    panel_style: str = "bold cyan on #0f1a26",
                    border_color: str = "cyan") -> None:
    layout = _build_layout(title, help_text, status_text, panel_style=panel_style, border_color=border_color)
    with Live(layout, console=console, screen=True, refresh_per_second=30):
        layout["body"].update(Align(renderable, align="center", vertical="middle"))
        while True:
            key = readchar.readkey()
            if key in (readchar.key.ENTER, getattr(readchar.key, "ESC", "\x1b"), readchar.key.BACKSPACE, "q", "Q"):
                break

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

def _paginate_loop_live(make_renderable_fn: Callable[[int, int, int], Any],
                        total_items: int,
                        page_size: int,
                        base_title: str,
                        help_text: str,
                        status_text: str = "",
                        *,
                        panel_style: str = "bold cyan on #0f1a26",
                        border_color: str = "cyan") -> None:
    if total_items <= 0:
        console.print("[bold red]No data to display.[/bold red]")
        input("Press Enter to return...")
        return
    index = 0
    max_index = (total_items - 1) // page_size * page_size
    # initial layout
    dynamic_title = f"{base_title} [1-{min(page_size, total_items)}/{total_items}]"
    layout = _build_layout(dynamic_title, help_text, status_text, panel_style=panel_style, border_color=border_color)
    with Live(layout, console=console, screen=True, refresh_per_second=30):
        while True:
            i_start = index
            i_end = min(index + page_size, total_items)
            # update header title with current range
            dynamic_title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
            header_panel = Panel(
                Align.center(Text(dynamic_title, style="app.title")),
                border_style=border_color,
                style=panel_style,
                padding=(0, 2),
            )
            layout["header"].update(header_panel)
            # update body with renderable
            renderable = make_renderable_fn(i_start, i_end, total_items)
            layout["body"].update(Align(renderable, align="center", vertical="middle"))
            # read key
            key = readchar.readkey()
            if key == readchar.key.RIGHT:
                index = 0 if index >= max_index else index + page_size
            elif key == readchar.key.LEFT:
                index = max_index if index == 0 else index - page_size
            elif key in (getattr(readchar.key, "ESC", "\x1b"), readchar.key.BACKSPACE, "q", "Q"):
                break

def paginate_students_table(students: List[Dict[str, Any]], base_title: str, page_size: int = 10) -> None:
    total = len(students)
    def make(i_start: int, i_end: int, total_items: int):
        title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
        return build_student_table(students[i_start:i_end], title=title)
    help_text = "Use ←/→ to navigate pages • Press q/Esc/Backspace to return"
    status_text = f"Students: {total}"
    _paginate_loop_live(make, total, page_size, base_title, help_text, status_text)

def paginate_rank_table(rows: List[Dict[str, Any]], base_title: str, page_size: int = 10) -> None:
    total = len(rows)
    def make(i_start: int, i_end: int, total_items: int):
        title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
        return build_rank_table(rows[i_start:i_end], title=title)
    help_text = "Use ←/→ to navigate pages • Press q/Esc/Backspace to return"
    status_text = f"Rows: {total}"
    _paginate_loop_live(make, total, page_size, base_title, help_text, status_text)

def paginate_section_summary(sections_map: Dict[str, List[Dict[str, Any]]], averages: Dict[str, float], base_title: str, page_size: int = 10) -> None:
    section_names = sorted(sections_map.keys())
    total = len(section_names)
    if total == 0:
        console.print("[bold red]No sections available.[/bold red]")
        input("Press Enter to return...")
        return
    def make(i_start: int, i_end: int, total_items: int):
        subset_names = section_names[i_start:i_end]
        subset_map = {sec: sections_map[sec] for sec in subset_names}
        title = f"{base_title} [{i_start+1}-{i_end}/{total_items}]"
        return build_section_summary_table(subset_map, averages, title=title)
    help_text = "Use ←/→ to navigate pages • Press q/Esc/Backspace to return"
    status_text = f"Sections: {total}"
    _paginate_loop_live(make, total, page_size, base_title, help_text, status_text)

def load_or_reload_data(config_path: Optional[str] = None) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    from rich.align import Align
    from rich.text import Text
    from rich.panel import Panel
    
    console.clear()
    
    chosen_path = config_path or prompt_str("Config path (default 'config.json'):", "config.json")
    
    # Live layout with centered progress
    header_title = "📂 DATA LOADING"
    help_text = "Please wait while we load and process your data..."
    status_text = f"Config: {chosen_path}"
    layout = _build_layout(header_title, help_text, status_text)
    with Live(layout, console=console, screen=True, refresh_per_second=30):
        with Progress(console=console) as progress:
            layout["body"].update(Align(progress, align="center", vertical="middle"))
            task1 = progress.add_task("[cyan]Loading configuration...", total=100)
            for _ in range(100):
                progress.update(task1, advance=1)
                sleep(0.005)
            config = load_config(chosen_path)
            
            task2 = progress.add_task("[cyan]Reading CSV data...", total=100)
            for _ in range(100):
                progress.update(task2, advance=1)
                sleep(0.005)
            students_raw = read_csv_data(config["file_paths"]["input_csv"], config)
            
            task3 = progress.add_task("[cyan]Computing weighted grades...", total=100)
            for _ in range(100):
                progress.update(task3, advance=1)
                sleep(0.005)
            students = compute_weighted_grades(students_raw, config["grade_weights"])
            
            task4 = progress.add_task("[cyan]Grouping by sections...", total=100)
            for _ in range(100):
                progress.update(task4, advance=1)
                sleep(0.005)
            sections = group_students_by_section(students)
    # Success summary in centered layout
    summary_lines = [
        "[good]Configuration loaded[/good]",
        f"[good]Loaded {len(students)} student records[/good]",
        "[good]Grades computed[/good]",
        f"[good]Organized into {len(sections)} sections[/good]",
    ]
    success_panel = Panel(Text.from_markup("\n".join(summary_lines)), title="✨ DATA LOADED SUCCESSFULLY ✨", border_style="green", padding=(1, 2))
    _show_in_layout(success_panel, "Data Loaded", status_text=f"Students: {len(students)}  |  Sections: {len(sections)}  |  Config: {chosen_path}")
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
    confirm = prompt_str(f"Confirm delete {student_id}? [y/N]:", "N").strip().lower()
    if confirm != "y":
        console.print("[warn]Cancelled.[/warn]")
        input("Press Enter to continue...")
        return students, sections
    if core_delete_student(sections, student_id):
        students = [s for s in students if s.get("student_id") != student_id]
        console.print(f"[good]Deleted student with ID {student_id}[/good]")
    else:
        console.print(f"[bad]No student found with ID {student_id}[/bad]")
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
    ║      █████╗  ██████╗ █████╗ ██████╗ ███████╗███╗   ███╗██╗    ║
    ║     ██╔══██╗██╔════╝██╔══██╗██╔══██╗██╔════╝████╗ ████║██║    ║
    ║     ███████║██║     ███████║██║  ██║█████╗  ██╔████╔██║██║    ║
    ║     ██╔══██║██║     ██╔══██║██║  ██║██╔══╝  ██║╚██╔╝██║██║    ║
    ║     ██║  ██║╚██████╗██║  ██║██████╔╝███████╗██║ ╚═╝ ██║██║    ║
    ║     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝    ║
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
def arrow_menu(title: str, options: Dict[str, str], level: int = 1, status_text: str = "") -> str:
    from rich.align import Align
    from rich.text import Text
    
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

    help_text = "↑/↓ Move  •  Enter Select  •  PgUp/PgDn/Home/End Jump  •  q/Esc Back"
    header_title = f"{icon}  {title}  {icon}"
    layout = _build_layout(header_title, help_text, status_text, panel_style=panel_style, border_color=border_color)

    def _make_table() -> Table:
        table = Table(
            title="[app.title]Select an Option[/app.title]",
            style=panel_style,
            show_header=True,
            header_style="bold yellow",
            border_style=border_color,
            expand=False
        )
        table.add_column("Key", justify="center", style="bold white", width=10)
        table.add_column("Option", justify="left", width=48)
        for i, (key, desc) in enumerate(options.items()):
            if i == selected:
                table.add_row(
                    f"▶ {key} ◀",
                    f"[good]{desc}[/good]",
                    style="on #1a3a3a"
                )
            else:
                table.add_row(f"  {key}  ", desc)
        return table

    with Live(layout, console=console, screen=True, refresh_per_second=30):
        while True:
            layout["body"].update(Align(_make_table(), align="center", vertical="middle"))
            key = readchar.readkey()
            if key == readchar.key.UP:
                selected = (selected - 1) % len(keys)
            elif key == readchar.key.DOWN:
                selected = (selected + 1) % len(keys)
            elif key in (getattr(readchar.key, "PAGE_UP", None), getattr(readchar.key, "HOME", None)):
                selected = 0
            elif key in (getattr(readchar.key, "PAGE_DOWN", None), getattr(readchar.key, "END", None)):
                selected = len(keys) - 1
            elif key == readchar.key.ENTER:
                return keys[selected]
            elif key in (getattr(readchar.key, "ESC", "\x1b"), "q", "Q"):
                last_val = list(options.values())[-1].lower()
                if last_val == "back":
                    return keys[-1]
                return keys[selected]

# =====================================
# Renderers (Showcase-integrated)
# =====================================
def view_overall_roster(students: List[Dict[str, Any]]) -> None:
    console.clear()
    filt = prompt_str("Filter by name contains (optional):", "")
    if filt:
        token = filt.strip().lower()
        filtered = [
            s for s in students
            if token in f"{str(s.get('first_name',''))} {str(s.get('last_name',''))}".lower()
        ]
    else:
        filtered = students
    paginate_students_table(filtered, base_title="Overall Roster", page_size=10)

def view_overall_distribution(students: List[Dict[str, Any]], config_path: str) -> None:
    console.clear()
    cfg = load_config(config_path)
    dist = calculate_distribution(students, cfg["thresholds"]["grade_letters"])
    table = build_distribution_table(dist, total=len(students), title="Overall Grade Distribution")
    status = _status_text_basic(students, None, config_path)
    _show_in_layout(table, "Overall Distribution", status_text=status)

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
    table = build_curve_table(curved[:preview], title="Curve Preview")
    status = _status_text_basic(students, None, None)
    _show_in_layout(table, "Curve Preview", status_text=status)

def view_improvement_insights(students: List[Dict[str, Any]]) -> None:
    console.clear()
    result = track_midterm_to_final_improvement(students)
    lines: List[str] = ["[bold]Midterm vs. Final Improvement Analysis:[/bold]"]
    if result["total_students"] == 0:
        lines.append("[bad]No midterm and final exam data available to analyze.[/bad]")
        panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
        status = _status_text_basic(students, None, None)
        _show_in_layout(panel, "Improvement Insights", status_text=status)
        return
    lines.append(f"- Total students analyzed: {result['total_students']}")
    lines.append(f"- Students who improved: {result['counts']['improved']} ({result['percentages']['improved']:.1f}%)")
    lines.append(f"- Students who stayed the same: {result['counts']['same']} ({result['percentages']['same']:.1f}%)")
    lines.append(f"- Students who declined: {result['counts']['declined']} ({result['percentages']['declined']:.1f}%)")
    if result["avg_improvement"] > 0:
        lines.append(f"- Average improvement among improvers: {result['avg_improvement']:.1f} points")
    if result["avg_decline"] > 0 and result["counts"]["declined"] > 0:
        lines.append(f"- Average decline among decliners: {result['avg_decline']:.1f} points")
    if result.get("suggestions"):
        lines.append("\n[bold yellow]SUGGESTIONS:[/bold yellow]")
        for s in result["suggestions"]:
            lines.append(f"- {s}")
    panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
    status = _status_text_basic(students, None, None)
    _show_in_layout(panel, "Improvement Insights", status_text=status)

def view_attendance_correlation_overall(students: List[Dict[str, Any]]) -> None:
    console.clear()
    threshold = prompt_float("Attendance threshold % (default 80):", 80.0, 0.0, 100.0)
    res = correlate_attendance_and_grades(students, threshold=float(threshold))
    lines: List[str] = ["[bold]Attendance-Grade Correlation (Overall):[/bold]"]
    if res["low_count"] == 0 and res["high_count"] == 0:
        lines.append("[bad]No attendance data available to analyze.[/bad]")
        panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
        status = _status_text_basic(students, None, None)
        _show_in_layout(panel, "Attendance Correlation", status_text=status)
        return
    lines.append(f"- Attendance Threshold: {res['threshold']:.0f}%")
    lines.append(f"- Low Attendance Group (<{res['threshold']:.0f}%): {res['low_count']} students")
    lines.append(f"- High Attendance Group (≥{res['threshold']:.0f}%): {res['high_count']} students")
    lines.append(f"- Low-attendance avg grade: {res['low_avg_grade']:.1f}%")
    lines.append(f"- High-attendance avg grade: {res['high_avg_grade']:.1f}%")
    lines.append(f"- Grade difference: {res['grade_difference']:.1f} points")
    if res.get("insights"):
        lines.append("\n[bold]Insights:[/bold]")
        for i in res["insights"]:
            lines.append(f"- {i}")
    if res.get("suggestions"):
        lines.append("\n[bold yellow]Suggestions:[/bold yellow]")
        for s in res["suggestions"]:
            lines.append(f"- {s}")
    panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
    status = _status_text_basic(students, None, None)
    _show_in_layout(panel, "Attendance Correlation", status_text=status)

def _select_section(sections: Dict[str, List[Dict[str, Any]]]) -> Optional[str]:
    if not sections:
        console.print("[bold red]No sections available.[/bold red]")
        input("Press Enter to return...")
        return None
    options = {str(i + 1): sec for i, sec in enumerate(sorted(sections.keys()))}
    options[str(len(options) + 1)] = "Back"
    choice = arrow_menu("Select Section", options, level=3, status_text=f"Sections: {len(sections)}")
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
    choice = arrow_menu(f"Sort {section}", sort_opts, level=3, status_text=f"Section: {section}  |  Students: {len(studs)}")
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
    choice = arrow_menu(f"Top/Bottom — {section}", opts, level=3, status_text=f"Section: {section}  |  Students: {len(studs)}")
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
    table = build_distribution_table(dist, total=len(studs), title=f"Grade Distribution — {section}")
    status = f"Section: {section}  |  Students: {len(studs)}"
    _show_in_layout(table, f"Distribution — {section}", status_text=status)

def section_hardest_topic(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    quiz_avgs, quiz_counts, hardest_quiz, lowest = get_quiz_averages(studs)
    table = build_hardest_topic_table(quiz_avgs, quiz_counts, hardest_quiz, title=f"Hardest Topic — {section}")
    status = f"Section: {section}  |  Students: {len(studs)}"
    _show_in_layout(table, f"Hardest Topic — {section}", status_text=status)

def view_quiz_comparison(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    avg_by_section, quiz_keys, lowest_per_quiz = get_sections_quiz_averages(sections)
    table = build_quiz_comparison_table(avg_by_section, quiz_keys, lowest_per_quiz, title="Quiz Averages Comparison")
    status = f"Sections: {len(sections)}"
    _show_in_layout(table, "Quiz Averages Comparison", status_text=status)

def section_improvement_insights(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    result = track_midterm_to_final_improvement(studs)
    lines: List[str] = [f"[bold]Improvement Analysis — {section}[/bold]"]
    if result["total_students"] == 0:
        lines.append("[bad]No midterm and final exam data available to analyze.[/bad]")
        panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
        status = f"Section: {section}  |  Students: {len(studs)}"
        _show_in_layout(panel, f"Improvement — {section}", status_text=status)
        return
    lines.append(f"- Total students analyzed: {result['total_students']}")
    lines.append(f"- Improved: {result['counts']['improved']} ({result['percentages']['improved']:.1f}%)")
    lines.append(f"- Same: {result['counts']['same']} ({result['percentages']['same']:.1f}%)")
    lines.append(f"- Declined: {result['counts']['declined']} ({result['percentages']['declined']:.1f}%)")
    if result["avg_improvement"] > 0:
        lines.append(f"- Avg improvement: {result['avg_improvement']:.1f} points")
    if result["avg_decline"] > 0 and result["counts"]["declined"] > 0:
        lines.append(f"- Avg decline (decliners): {result['avg_decline']:.1f} points")
    if result.get("suggestions"):
        lines.append("\n[bold yellow]Suggestions:[/bold yellow]")
        for s in result["suggestions"]:
            lines.append(f"- {s}")
    panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
    status = f"Section: {section}  |  Students: {len(studs)}"
    _show_in_layout(panel, f"Improvement — {section}", status_text=status)

def section_attendance_correlation(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    section = _select_section(sections)
    if not section:
        return
    studs = sections.get(section, [])
    threshold = prompt_float("Attendance threshold % (default 80):", 80.0, 0.0, 100.0)
    res = correlate_attendance_and_grades(studs, threshold=float(threshold))
    lines: List[str] = [f"[bold]Attendance-Grade Correlation — {section}[/bold]"]
    if res["low_count"] == 0 and res["high_count"] == 0:
        lines.append("[bad]No attendance data available to analyze.[/bad]")
        panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
        status = f"Section: {section}  |  Students: {len(studs)}"
        _show_in_layout(panel, f"Attendance — {section}", status_text=status)
        return
    lines.append(f"- Attendance Threshold: {res['threshold']:.0f}%")
    lines.append(f"- Low Attendance Group (<{res['threshold']:.0f}%): {res['low_count']} students")
    lines.append(f"- High Attendance Group (≥{res['threshold']:.0f}%): {res['high_count']} students")
    lines.append(f"- Low-attendance avg grade: {res['low_avg_grade']:.1f}%")
    lines.append(f"- High-attendance avg grade: {res['high_avg_grade']:.1f}%")
    lines.append(f"- Grade difference: {res['grade_difference']:.1f} points")
    if res.get("insights"):
        lines.append("\n[bold]Insights:[/bold]")
        for i in res["insights"]:
            lines.append(f"- {i}")
    if res.get("suggestions"):
        lines.append("\n[bold yellow]Suggestions:[/bold yellow]")
        for s in res["suggestions"]:
            lines.append(f"- {s}")
    panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
    status = f"Section: {section}  |  Students: {len(studs)}"
    _show_in_layout(panel, f"Attendance — {section}", status_text=status)

def view_compare_sections_insights(sections: Dict[str, List[Dict[str, Any]]]) -> None:
    console.clear()
    res = compare_sections(sections)
    lines: List[str] = ["[bold]Compare Sections — Text Insights[/bold]"]
    if not res.get("insights"):
        lines.append("[bad]No insights available.[/bad]")
    else:
        for line in res["insights"]:
            lines.append(f"- {line}")
    panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
    status = f"Sections: {len(sections)}"
    _show_in_layout(panel, "Compare Sections", status_text=status)

# =====================================
# Section CRUD Management
# =====================================
def _prompt_student_fields(existing: Optional[Dict[str, Any]] = None, preselected_section: Optional[str] = None) -> Dict[str, Any]:
    existing = existing or {}
    student_id = prompt_str(f"Student ID ({existing.get('student_id','')}):", existing.get("student_id", "") or "")
    first_name = prompt_str(f"First Name ({existing.get('first_name','')}):", existing.get("first_name", "") or "")
    middle_name = prompt_str(f"Middle Name ({existing.get('middle_name','')}):", existing.get("middle_name", "") or "")
    last_name = prompt_str(f"Last Name ({existing.get('last_name','')}):", existing.get("last_name", "") or "")
    section = preselected_section if preselected_section else prompt_str(f"Section ({existing.get('section','')}):", existing.get("section", "") or "")
    # Scores
    q1 = prompt_int(f"Quiz1 ({existing.get('quiz1','')}):", int(existing.get("quiz1", 0)))
    q2 = prompt_int(f"Quiz2 ({existing.get('quiz2','')}):", int(existing.get("quiz2", 0)))
    q3 = prompt_int(f"Quiz3 ({existing.get('quiz3','')}):", int(existing.get("quiz3", 0)))
    q4 = prompt_int(f"Quiz4 ({existing.get('quiz4','')}):", int(existing.get("quiz4", 0)))
    q5 = prompt_int(f"Quiz5 ({existing.get('quiz5','')}):", int(existing.get("quiz5", 0)))
    midterm = prompt_int(f"Midterm ({existing.get('midterm','')}):", int(existing.get("midterm", 0)))
    final = prompt_int(f"Final ({existing.get('final','')}):", int(existing.get("final", 0)))
    attendance = prompt_float(f"Attendance % ({existing.get('attendance_percent','')}):", float(existing.get("attendance_percent", 0.0)))
    return {
        "student_id": student_id,
        "first_name": first_name,
        "middle_name": middle_name,
        "last_name": last_name,
        "section": section,
        "quiz1": q1, "quiz2": q2, "quiz3": q3, "quiz4": q4, "quiz5": q5,
        "midterm": midterm, "final": final,
        "attendance_percent": attendance,
    }

def _find_student_by_id(seq: List[Dict[str, Any]], student_id: str) -> Optional[Dict[str, Any]]:
    for s in seq:
        if str(s.get("student_id", "")).lower() == student_id.lower():
            return s
    return None

def _replace_in_students_list(students: List[Dict[str, Any]], updated: Dict[str, Any]) -> List[Dict[str, Any]]:
    new_list: List[Dict[str, Any]] = []
    target_id = str(updated.get("student_id", ""))
    for s in students:
        if str(s.get("student_id", "")) == target_id:
            new_list.append(updated)
        else:
            new_list.append(s)
    return new_list

def add_student_to_section(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], section: str, config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    cfg = load_config(config_path)
    base = _prompt_student_fields(preselected_section=section)
    base = compute_weighted_grades([base], cfg["grade_weights"])[0]
    core_insert_student(sections, base)
    students.append(base)
    _show_in_layout(Panel(Text.from_markup(f"[good]Inserted {base.get('first_name','')} {base.get('last_name','')} into {section}[/good]"), border_style="green"),
                    "Insert Student", status_text=f"Section: {section}")
    return students, sections

def edit_student_in_section(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], section: str, config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    cfg = load_config(config_path)
    sid = prompt_str("Enter Student ID to edit:", "")
    if not sid:
        return students, sections
    target = _find_student_by_id(sections.get(section, []), sid)
    if not target:
        _show_in_layout(Panel(Text.from_markup(f"[bad]No student with ID {sid} in {section}[/bad]"), border_style="red"), "Edit Student", status_text=f"Section: {section}")
        return students, sections
    updated = _prompt_student_fields(existing=target, preselected_section=section)
    updated = compute_weighted_grades([updated], cfg["grade_weights"])[0]
    # Update in sections list
    for i, s in enumerate(sections[section]):
        if str(s.get("student_id","")) == sid:
            sections[section][i] = updated
            break
    # Update in global students list
    students = _replace_in_students_list(students, updated)
    _show_in_layout(Panel(Text.from_markup(f"[good]Updated {updated.get('first_name','')} {updated.get('last_name','')}[/good]"), border_style="green"),
                    "Edit Student", status_text=f"Section: {section}")
    return students, sections

def delete_student_in_section(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], section: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    sid = prompt_str("Enter Student ID to delete:", "")
    if not sid:
        return students, sections
    if not _find_student_by_id(sections.get(section, []), sid):
        _show_in_layout(Panel(Text.from_markup(f"[bad]No student with ID {sid} in {section}[/bad]"), border_style="red"),
                        "Delete Student", status_text=f"Section: {section}")
        return students, sections
    confirm = prompt_str(f"Confirm delete {sid} from {section}? [y/N]:", "N").strip().lower()
    if confirm != "y":
        _show_in_layout(Panel(Text.from_markup("[warn]Cancelled.[/warn]"), border_style="yellow"), "Delete Student", status_text=f"Section: {section}")
        return students, sections
    if core_delete_student(sections, sid):
        students = [s for s in students if str(s.get("student_id","")) != sid]
        _show_in_layout(Panel(Text.from_markup(f"[good]Deleted {sid}[/good]"), border_style="green"), "Delete Student", status_text=f"Section: {section}")
    else:
        _show_in_layout(Panel(Text.from_markup(f"[bad]Failed to delete {sid}[/bad]"), border_style="red"), "Delete Student", status_text=f"Section: {section}")
    return students, sections

def section_manage_crud(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    console.clear()
    section = _select_section(sections)
    if not section:
        return students, sections, config_path
    opts = {
        "1": "Add Student",
        "2": "Edit Student",
        "3": "Delete Student",
        "4": "Back"
    }
    while True:
        choice = arrow_menu(f"Manage Section — {section}", opts, level=3, status_text=f"Section: {section}  |  Students: {len(sections.get(section, []))}")
        if choice == "4":
            break
        elif choice == "1":
            students, sections = add_student_to_section(students, sections, section, config_path)
        elif choice == "2":
            students, sections = edit_student_in_section(students, sections, section, config_path)
        elif choice == "3":
            students, sections = delete_student_in_section(students, sections, section)
    return students, sections, config_path

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
        choice = arrow_menu("Lookup Individual Student", options, level=3, status_text=f"Students: {len(students)}")
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
    choice = arrow_menu("Overall Histograms", options, level=3, status_text=f"Students: {len(students)}")
    
    has_display = _is_display_available()
    display_msg = " (and displayed)" if has_display else ""
    
    if choice == "1":
        file_path = plot_grade_histogram(students, "weighted_grade", "Overall Weighted Grade Distribution")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, "Weighted Grade Distribution", status_text=f"Students: {len(students)}")
    elif choice == "2":
        file_path = plot_combined_histogram(students, ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5"], "Quiz Scores Distribution")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, "Quiz Scores Distribution", status_text=f"Students: {len(students)}")
    elif choice == "3":
        file_path = plot_combined_histogram(students, ["midterm", "final"], "Midterm vs Final Exam Distribution")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, "Midterm vs Final", status_text=f"Students: {len(students)}")
    elif choice == "4":
        file_path = plot_grade_histogram(students, "attendance_percent", "Attendance Distribution")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, "Attendance Distribution", status_text=f"Students: {len(students)}")
    elif choice == "5":
        file_path = plot_combined_histogram(
            students,
            ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade"],
            "All Scores including Weighted Grade"
        )
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, "All Scores Combined", status_text=f"Students: {len(students)}")
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
        lines = [
            f"[good]Saved:[/good] {f1}",
            f"[good]Saved:[/good] {f2}",
            f"[good]Saved:[/good] {f3}",
            f"[good]Saved:[/good] {f4}",
            f"[good]Saved:[/good] {f5}",
        ]
        if has_display:
            lines.append("[good]All plots displayed (if GUI available).[/good]")
        panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
        _show_in_layout(panel, "Generated All Plots", status_text=f"Students: {len(students)}")

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
    choice = arrow_menu(f"Section Histograms - {section}", options, level=3, status_text=f"Section: {section}  |  Students: {len(studs)}")
    
    has_display = _is_display_available()
    display_msg = " (and displayed)" if has_display else ""
    
    if choice == "1":
        file_path = plot_grade_histogram(studs, "weighted_grade", f"Weighted Grade Distribution - {section}")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, f"Weighted Grade — {section}", status_text=f"Section: {section}")
    elif choice == "2":
        file_path = plot_combined_histogram(studs, ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5"], f"Quiz Scores Distribution - {section}")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, f"Quiz Scores — {section}", status_text=f"Section: {section}")
    elif choice == "3":
        file_path = plot_combined_histogram(studs, ["midterm", "final"], f"Midterm vs Final - {section}")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, f"Midterm vs Final — {section}", status_text=f"Section: {section}")
    elif choice == "4":
        file_path = plot_grade_histogram(studs, "attendance_percent", f"Attendance Distribution - {section}")
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, f"Attendance — {section}", status_text=f"Section: {section}")
    elif choice == "5":
        file_path = plot_combined_histogram(
            studs,
            ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade"],
            f"All Scores - {section}"
        )
        msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
        _show_in_layout(msg, f"All Scores — {section}", status_text=f"Section: {section}")
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
        lines = [
            "[good]All plots saved to output/plots/[/good]",
            ("[good]Displayed as well.[/good]" if has_display else "[warn]No display detected; files saved only.[/warn]"),
        ]
        panel = Panel(Text.from_markup("\n".join(lines)), border_style="cyan")
        _show_in_layout(panel, f"Generated All Plots — {section}", status_text=f"Section: {section}")

def plot_custom_histogram(students: List[Dict[str, Any]]) -> None:
    console.clear()
    console.print("[bold cyan]Select column to plot:[/bold cyan]")
    console.print("Available: quiz1, quiz2, quiz3, quiz4, quiz5, midterm, final, weighted_grade, attendance_percent")
    key = prompt_str("Enter column name:", "weighted_grade")
    
    if key not in ["quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "weighted_grade", "attendance_percent"]:
        msg = Panel(Text.from_markup(f"[bad]Invalid column: {key}[/bad]"), border_style="cyan")
        _show_in_layout(msg, "Custom Histogram", status_text=f"Students: {len(students)}")
        return
    
    has_display = _is_display_available()
    display_msg = " (and displayed)" if has_display else ""
    
    file_path = plot_grade_histogram(students, key)
    msg = Panel(Text.from_markup(f"[good]Plot saved to: {file_path}{display_msg}[/good]"), border_style="cyan")
    _show_in_layout(msg, f"Custom Histogram — {key}", status_text=f"Students: {len(students)}")

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
        "1.g": "Improvement Insights (Midterm→Final)",
        "1.h": "Attendance-Grade Correlation (Overall)",
        "1.i": "Back"
    }
    while True:
        status = _status_text_basic(students, sections, config_path)
        choice = arrow_menu("Course Dashboard", options, level=2, status_text=status)
        if choice == "1.i":
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
        elif choice == "1.g":
            view_improvement_insights(students)
        elif choice == "1.h":
            view_attendance_correlation_overall(students)
    return students, sections, config_path

def section_analytics(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "2.a": "View Section Table",
        "2.b": "Sort a Section",
        "2.c": "Top/Bottom N in Section",
        "2.d": "Section Grade Distribution",
        "2.e": "Hardest Topic per Section",
        "2.f": "Quiz Averages Comparison (All Sections)",
        "2.g": "Compare Sections (Text Insights)",
        "2.h": "Section Improvement Insights",
        "2.i": "Section Attendance Correlation",
        "2.j": "Section Histograms",
        "2.k": "Manage Section (CRUD)",
        "2.l": "Back"
    }
    while True:
        status = _status_text_basic(students, sections, config_path)
        choice = arrow_menu("Section Analytics", options, level=2, status_text=status)
        if choice == "2.l":
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
            view_compare_sections_insights(sections)
        elif choice == "2.h":
            section_improvement_insights(sections)
        elif choice == "2.i":
            section_attendance_correlation(sections)
        elif choice == "2.j":
            plot_section_histograms(sections)
        elif choice == "2.k":
            students, sections, config_path = section_manage_crud(students, sections, config_path)
    return students, sections, config_path

def student_reports(students: List[Dict[str, Any]], sections: Dict[str, List[Dict[str, Any]]], config_path: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]], str]:
    options = {
        "3.a": "View 'At-Risk' Student List",
        "3.b": "Export Section Reports to CSV",
        "3.c": "Look Up Individual Student",
        "3.d": "Back"
    }
    while True:
        status = _status_text_basic(students, sections, config_path)
        choice = arrow_menu("Student Reports", options, level=2, status_text=status)
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
        status = _status_text_basic(students, sections, config_path)
        choice = arrow_menu("Tools & Utilities", options, level=2, status_text=status)
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
        status = _status_text_basic(students, sections, config_path)
        choice = arrow_menu("Main Menu", options, level=1, status_text=status)
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
