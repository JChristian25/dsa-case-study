from typing import Any, Dict, Iterable, List
from rich.table import Table
from rich import box


def _quiz_keys() -> List[str]:
    return [f"quiz{i}" for i in range(1, 6)]


def _format_cell_value(value: Any) -> str:
    """Format cell values; show literal 'None' (dim) for missing."""
    return "[dim]None[/dim]" if value is None else f"{value}"

def _styled_table(title: str, caption: str | None = None) -> Table:
    t = Table(
        title=title,
        header_style="bold cyan",
        title_style="bold cyan",
        border_style="cyan",
        box=box.ROUNDED,          # rounded corners
        highlight=True,           # highlight changed cells/selections
        row_styles=["", "dim"],   # zebra striping
        expand=True,              # use full terminal width
    )
    if caption:
        t.caption = caption
        t.caption_style = "dim"
    return t

def _color_for_grade(v: float) -> str:
    """Color mapping for 0-100 grades."""
    if v is None:
        return ""
    try:
        val = float(v)
    except Exception:
        return ""
    if val >= 90:
        return "green"
    if val >= 80:
        return "cyan"
    if val >= 70:
        return "yellow"
    if val >= 60:
        return "orange3"
    return "red"


def _colorize_percent(v: Any, decimals: int = 1, suffix: str = "") -> str:
    if v is None:
        return _format_cell_value(None)
    try:
        val = float(v)
    except Exception:
        return _format_cell_value(v)
    color = _color_for_grade(val)
    formatted = f"{val:.{decimals}f}{suffix}"
    return f"[{color}]{formatted}[/]" if color else formatted


def _progress_bar(percent: Any, width: int = 16) -> str:
    if percent is None:
        return _format_cell_value(None)
    try:
        p = max(0.0, min(100.0, float(percent)))
    except Exception:
        return _format_cell_value(percent)
    filled = int(round(p / 100.0 * width))
    empty = width - filled
    color = _color_for_grade(p)
    bar = f"[{color}]" + ("█" * filled) + ("░" * empty) + "[/]"
    return f"{bar} {p:.0f}%"


def _styled_table(title: str, caption: str | None = None) -> Table:
    """Create a consistently styled rich.Table for all renderers."""
    t = Table(
        title=title,
        header_style="bold cyan",
        title_style="bold cyan",
        border_style="cyan",
        box=box.ROUNDED,
        highlight=True,
        row_styles=["", "dim"],
        expand=True,
    )
    if caption:
        t.caption = caption
        t.caption_style = "dim"
    return t


def build_student_table(students: Iterable[Dict[str, Any]], title: str = "Students") -> Table:
    table = _styled_table(title)
    headers: List[List[str]] = [
        ["ID", "left"], ["Last", "left"], ["First", "left"], ["Section", "left"],
        ["Q1", "right"], ["Q2", "right"], ["Q3", "right"], ["Q4", "right"], ["Q5", "right"],
        ["Quiz Avg", "right"], ["Midterm", "right"], ["Final", "right"], ["Attendance", "right"], ["Weighted", "right"],
    ]
    for col, justify in headers:
        table.add_column(col, justify=justify)

    q_keys = _quiz_keys()
    for s in students:
        quizzes = [s.get(k) for k in q_keys]
        vals = [v for v in quizzes if isinstance(v, (int, float))]
        quiz_avg = round(sum(vals) / len(q_keys), 2) if vals else ""
        row = [
            _format_cell_value(s.get("student_id", "")),
            _format_cell_value(s.get("last_name", "")),
            _format_cell_value(s.get("first_name", "")),
            _format_cell_value(s.get("section", "")),
            *[_format_cell_value(v) for v in quizzes],
            (_colorize_percent(quiz_avg) if quiz_avg != "" else _format_cell_value(None)),
            _colorize_percent(s.get('midterm', None)),
            _colorize_percent(s.get('final', None)),
            _progress_bar(s.get('attendance_percent', None)),
            _colorize_percent(s.get('weighted_grade', None), decimals=2),
        ]
        table.add_row(*row)
    return table


def build_distribution_table(distribution: Dict[str, int], total: int, title: str = "Grade Distribution") -> Table:
    table = _styled_table(title)
    table.add_column("Grade", justify="center")
    table.add_column("Count", justify="right")
    table.add_column("Percent", justify="right")
    table.add_column("Bar", justify="left")

    # Stable order A > B > C > D > -D
    order = ["A", "B", "C", "D", "-D"]
    for grade in order:
        count = distribution.get(grade, 0)
        pct = (count / total * 100) if total else 0
        color_map = {"A": "green", "B": "cyan", "C": "yellow", "D": "orange3", "-D": "red"}
        color = color_map.get(grade, "white")
        bar = (f"[{color}]" + ("█" * max(1, int(pct // 2))) + "[/]") if count else ""
        table.add_row(f"[{color}]{grade}[/]", str(count), f"[{color}]{pct:.1f}%[/]", bar)
    return table


def build_section_summary_table(section_map: Dict[str, List[Dict[str, Any]]], averages: Dict[str, float], title: str = "Sections Summary") -> Table:
    table = _styled_table(title)
    table.add_column("Section", justify="left")
    table.add_column("Students", justify="right")
    table.add_column("Avg Weighted", justify="right")
    for section, studs in sorted(section_map.items()):
        avg = averages.get(section, 0.0)
        table.add_row(section, str(len(studs)), _colorize_percent(avg, decimals=2))
    return table


def build_rank_table(rows: List[Dict[str, Any]], title: str = "Ranking") -> Table:
    table = _styled_table(title)
    table.add_column("Rank", justify="center")
    table.add_column("Student", justify="left")
    table.add_column("Section", justify="left")
    table.add_column("Weighted", justify="right")
    for r in rows:
        name = f"{r.get('first_name','')} {r.get('last_name','')}".strip()
        table.add_row(
            str(r.get("rank", "")), name, str(r.get("section", "")), _colorize_percent(r.get('weighted_grade', None), decimals=2)
        )
    return table


def build_curve_table(students: Iterable[Dict[str, Any]], title: str = "Curved Grades") -> Table:
    table = _styled_table(title)
    table.add_column("Student", justify="left")
    table.add_column("Section", justify="left")
    table.add_column("Original", justify="right")
    table.add_column("Curved", justify="right")
    for s in students:
        orig = s.get("weighted_grade")
        curved = s.get("curved_grade")
        name = f"{s.get('last_name','')}, {s.get('first_name','')}".strip(', ')
        table.add_row(
            _format_cell_value(name),
            _format_cell_value(s.get("section", "")),
            _colorize_percent(orig, decimals=2),
            _colorize_percent(curved, decimals=2),
        )
    return table


def build_hardest_topic_table(quiz_averages: Dict[str, float], quiz_counts: Dict[str, int], hardest_quiz: str, title: str = "Hardest Topic Analysis") -> Table:
    table = _styled_table(title)
    table.add_column("Quiz", justify="left")
    table.add_column("Avg %", justify="right")
    table.add_column("Count", justify="right")
    table.add_column("Note", justify="left")
    for quiz in sorted(quiz_averages.keys()):
        avg = quiz_averages[quiz]
        cnt = quiz_counts.get(quiz, 0)
        is_lowest = (quiz == hardest_quiz)
        note = "[bold red]lowest[/]" if is_lowest else ""
        avg_cell = _colorize_percent(avg, decimals=1, suffix="%")
        table.add_row(quiz.replace('_', ' ').title(), avg_cell, str(cnt), note)
    return table


def build_quiz_comparison_table(avg_by_section: Dict[str, Dict[str, float]], quiz_keys: List[str], lowest_per_quiz: Dict[str, Dict[str, Any]], title: str = "Quiz Averages by Section") -> Table:
    # Dynamic columns with sections
    sections = sorted(avg_by_section.keys())
    table = _styled_table(title)
    table.add_column("Quiz", justify="left")
    for sec in sections:
        table.add_column(sec, justify="right")
    table.add_column("Lowest", justify="left")

    for quiz in quiz_keys:
        row: List[str] = [quiz.replace('_', ' ').title()]
        for sec in sections:
            val = avg_by_section.get(sec, {}).get(quiz, 0.0)
            low_info = lowest_per_quiz.get(quiz, {})
            is_lowest = (sec == low_info.get("section"))
            cell = _colorize_percent(val, decimals=0, suffix="%")
            if is_lowest:
                cell = f"[bold]{cell}[/]"
            row.append(cell)
        low_info = lowest_per_quiz.get(quiz, {})
        low_sec = low_info.get("section", "")
        low_val = low_info.get("avg", 0.0)
        row.append(f"{low_sec} ({low_val:.0f}%)" if low_sec else "")
        table.add_row(*row)
    return table
