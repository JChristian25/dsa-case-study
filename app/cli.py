from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from time import sleep
import os
import sys

console = Console()

# =====================================
# Animated Title (will change)
# =====================================
def animated_title():
    title_text = "📊 Academic Analytics Lite 📊"
    fade_colors = ["cyan", "white"]
    bg_style = "on #0f1a26"

    for _ in range(3):
        for color in fade_colors:
            console.clear()
            console.print(
                Panel(
                    title_text,
                    style=f"bold {color} {bg_style}",
                    expand=False,
                    border_style="cyan"
                )
            )
            sleep(0.8)

    console.clear()
    console.print(
        Panel(
            title_text,
            style=f"bold cyan {bg_style}",
            expand=False,
            border_style="cyan"
        )
    )

# =====================================
# Menu Design (number/letter-based)
# =====================================
def submenu(title, options):
    while True:
        console.clear()
        console.print(Panel(f"📂 {title}", style="bold cyan on #0f1a26", expand=False))

        table = Table(title="Select an Option", style="bold cyan")
        table.add_column("Option", justify="center")
        table.add_column("Description", justify="left")

        for key, desc in options.items():
            table.add_row(key, desc)

        console.print(table)
        console.print("[dim]Enter your choice (e.g., a) or 0 to go back.[/dim]")

        choice = input("Your choice: ").strip().lower()
        if choice == "0":
            return None
        elif choice in options:
            return choice
        else:
            console.print("[red]Invalid input! Please enter a valid option.[/red]")
            sleep(1)

# =====================================
# Options
# =====================================
def course_dashboard():
    options = {
        "a": "View Overall Summary",
        "b": "View Grade Histogram",
        "c": "View Grade Box Plot",
        "d": "View Improvement Insights",
        "e": "Back to Main Menu"
    }
    while True:
        choice = submenu("OPTION 1: COURSE DASHBOARD", options)
        if choice is None or choice == "e":
            break
        console.print(f"[bold green]Option selected: {options[choice]}[/bold green]")
        sleep(1)

def section_analytics():
    options = {
        "a": "Compare All Sections",
        "b": "View Report for Specific Section",
        "c": "Back to Main Menu"
    }
    while True:
        choice = submenu("OPTION 2: SECTION ANALYTICS", options)
        if choice is None or choice == "c":
            break
        console.print(f"[bold green]Option selected: {options[choice]}[/bold green]")
        sleep(1)

def student_reports():
    options = {
        "a": "View 'At-Risk' Student List",
        "b": "Export 'At-Risk' List to CSV",
        "c": "Look Up Individual Student",
        "d": "Back to Main Menu"
    }
    while True:
        choice = submenu("OPTION 3: STUDENT REPORTS", options)
        if choice is None or choice == "d":
            break
        console.print(f"[bold green]Option selected: {options[choice]}[/bold green]")
        sleep(1)

def tools_utilities():
    options = {
        "a": "Apply Grade Curve",
        "b": "Run Analytics (NumPy Version)",
        "c": "Back to Main Menu"
    }
    while True:
        choice = submenu("OPTION 4: TOOLS & UTILITIES", options)
        if choice is None or choice == "c":
            break
        console.print(f"[bold green]Option selected: {options[choice]}[/bold green]")
        sleep(1)

# =====================================
# Main Menu
# =====================================
def run_menu():
    animated_title()
    menu_options = {
        "1": "Course Dashboard",
        "2": "Section Analytics",
        "3": "Student Reports",
        "4": "Tools & Utilities",
        "5": "Exit"
    }

    while True:
        console.clear()
        console.print(Panel("📊 Academic Analytics Lite 📊", style="bold cyan on #0f1a26", expand=False))

        table = Table(title="MAIN MENU", style="bold cyan")
        table.add_column("Option", justify="center")
        table.add_column("Description", justify="left")

        for key, desc in menu_options.items():
            table.add_row(key, desc)

        console.print(table)
        console.print("[dim]Enter the number of your choice.[/dim]")

        choice = input("Your choice: ").strip()
        if choice in menu_options:
            if choice == "1":
                course_dashboard()
            elif choice == "2":
                section_analytics()
            elif choice == "3":
                student_reports()
            elif choice == "4":
                tools_utilities()
            elif choice == "5":
                console.print("[bold green]Exiting program. Goodbye![/bold green]")
                sys.exit()
        else:
            console.print("[red]Invalid input! Please enter a valid number.[/red]")
            sleep(1)

# =====================================
# Main Execution
# =====================================
if __name__ == "__main__":
    run_menu()
