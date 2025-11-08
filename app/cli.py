from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from time import sleep
import sys
import readchar
import matplotlib.pyplot as plt
import numpy as np
import csv

console = Console()

# =====================================
# Animated Title (might change)
# =====================================
def animated_title():
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
def arrow_menu(title, options, level=1):
    """
    level: 1 = main, 2 = submenu, 3 = sub-submenu
    """
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
# Placeholder functions
# =====================================
def view_overall_summary():
    console.clear()
    console.print("[bold yellow]Course Average: 85[/bold yellow]")
    console.print("[bold yellow]Median: 87[/bold yellow]")
    console.print("[bold yellow]High: 100, Low: 50[/bold yellow]")
    console.print("[bold yellow]Grade Distribution and Percentiles: ...[/bold yellow]")
    input("Press Enter to return...")

def view_grade_histogram():
    console.clear()
    console.print("[bold yellow]Generating Grade Histogram...[/bold yellow]")
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            sleep(0.02)
    scores = np.random.randint(50, 101, size=50)
    plt.hist(scores, bins=10, color="skyblue", edgecolor="black")
    plt.title("Grade Histogram")
    plt.xlabel("Scores")
    plt.ylabel("Frequency")
    plt.show()

def view_grade_boxplot():
    console.clear()
    console.print("[bold yellow]Generating Grade Box Plot...[/bold yellow]")
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing...", total=100)
        for _ in range(100):
            progress.update(task, advance=1)
            sleep(0.02)
    scores = np.random.randint(50, 101, size=50)
    plt.boxplot(scores)
    plt.title("Grade Box Plot")
    plt.show()

def improvement_insights():
    console.clear()
    console.print("[bold yellow]Improvement insights from Canva presentation...[/bold yellow]")
    input("Press Enter to return...")

def compare_all_sections():
    console.clear()
    console.print("[bold yellow]Side-by-side section table...[/bold yellow]")
    input("Press Enter to return...")

def view_specific_section():
    console.clear()
    section_name = input("Enter section name: ")
    console.print(f"[bold yellow]Report for section {section_name}...[/bold yellow]")
    input("Press Enter to return...")

def view_at_risk_list():
    console.clear()
    console.print("[bold yellow]At-Risk Students:[/bold yellow]\n- Student 1\n- Student 2\n- Student 3")
    input("Press Enter to return...")

def export_at_risk_csv():
    console.clear()
    data = [["ID","Name","Status"],[1,"Student 1","At-Risk"],[2,"Student 2","At-Risk"]]
    with open("at_risk.csv","w",newline="") as f:
        writer = csv.writer(f)
        writer.writerows(data)
    console.print("[bold green]At-Risk list exported to at_risk.csv[/bold green]")
    input("Press Enter to return...")

def apply_grade_curve():
    console.clear()
    options = {"1": "Flat", "2": "Normalize", "3": "Back"}  # Keep Back
    # Use level=3 to get darker cyan
    choice = arrow_menu("Apply Grade Curve", options, level=3)
    
    if choice == "3":  # Back selected
        return  # Go back to Tools & Utilities
    
    console.print(f"[bold green]Selected curve: {options[choice]}[/bold green]")
    input("Press Enter to return to Tools & Utilities...")


def run_numpy_analytics():
    console.clear()
    scores = np.random.randint(50,101,50)
    console.print(f"[bold yellow]Mean: {np.mean(scores)}, Median: {np.median(scores)}, Std: {np.std(scores)}[/bold yellow]")
    input("Press Enter to return...")

# =====================================
# Lookup Student Submenu
# =====================================
def lookup_student():
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
            lookup_by_id()
        elif choice == "2":
            lookup_by_first_name()
        elif choice == "3":
            lookup_by_middle_name()
        elif choice == "4":
            lookup_by_last_name()

def lookup_by_id():
    console.clear()
    student_id = input("Enter Student ID: ")
    console.print(f"[bold yellow]Searching for student with ID {student_id}...[/bold yellow]")
    input("Press Enter to return to Lookup Menu...")

def lookup_by_first_name():
    console.clear()
    first_name = input("Enter First Name: ")
    console.print(f"[bold yellow]Searching for student with first name '{first_name}'...[/bold yellow]")
    input("Press Enter to return to Lookup Menu...")

def lookup_by_middle_name():
    console.clear()
    middle_name = input("Enter Middle Name: ")
    console.print(f"[bold yellow]Searching for student with middle name '{middle_name}'...[/bold yellow]")
    input("Press Enter to return to Lookup Menu...")

def lookup_by_last_name():
    console.clear()
    last_name = input("Enter Last Name: ")
    console.print(f"[bold yellow]Searching for student with last name '{last_name}'...[/bold yellow]")
    input("Press Enter to return to Lookup Menu...")

# =====================================
# Submenus
# =====================================
def course_dashboard():
    options = {"1.a": "View Overall Summary", "1.b": "View Grade Histogram",
               "1.c": "View Grade Box Plot", "1.d": "View Improvement Insights",
               "1.e": "Back to Main Menu"}
    while True:
        choice = arrow_menu("Course Dashboard", options, level=2)
        if choice == "1.e":
            break
        elif choice == "1.a":
            view_overall_summary()
        elif choice == "1.b":
            view_grade_histogram()
        elif choice == "1.c":
            view_grade_boxplot()
        elif choice == "1.d":
            improvement_insights()

def section_analytics():
    options = {"2.a": "Compare All Sections", "2.b": "View Report for Specific Section",
               "2.e": "Back to Main Menu"}
    while True:
        choice = arrow_menu("Section Analytics", options, level=2)
        if choice == "2.e":
            break
        elif choice == "2.a":
            compare_all_sections()
        elif choice == "2.b":
            view_specific_section()

def student_reports():
    options = {"3.a": "View 'At-Risk' Student List", "3.b": "Export 'At-Risk' List to CSV",
               "3.c": "Look Up Individual Student", "3.d": "Back to Main Menu"}
    while True:
        choice = arrow_menu("Student Reports", options, level=2)
        if choice == "3.d":
            break
        elif choice == "3.a":
            view_at_risk_list()
        elif choice == "3.b":
            export_at_risk_csv()
        elif choice == "3.c":
            lookup_student()

def tools_utilities():
    options = {"4.a": "Apply Grade Curve", "4.b": "Run Analytics (NumPy Version)",
               "4.c": "Back to Main Menu"}
    while True:
        choice = arrow_menu("Tools & Utilities", options, level=2)
        if choice == "4.c":
            break
        elif choice == "4.a":
            apply_grade_curve()
        elif choice == "4.b":
            run_numpy_analytics()

# =====================================
# Main Menu
# =====================================
def run_menu():
    animated_title()
    options = {"1": "Course Dashboard", "2": "Section Analytics",
               "3": "Student Reports", "4": "Tools & Utilities", "5": "Exit"}
    while True:
        choice = arrow_menu("Main Menu", options, level=1)
        if choice == "1":
            course_dashboard()
        elif choice == "2":
            section_analytics()
        elif choice == "3":
            student_reports()
        elif choice == "4":
            tools_utilities()
        elif choice == "5":
            console.clear()
            console.print("[bold green]Exiting program. Goodbye![/bold green]")
            sys.exit()

# =====================================
# Main Execution
# =====================================
if __name__ == "__main__":
    run_menu()
