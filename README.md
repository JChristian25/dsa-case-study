<div align="center">
  <img src="Polytechnic_University_of_the_Philippines_Quezon_City_Logo.png" alt="PUP QC logo" width="96" />
  <h1>Academic Analytics Lite</h1>
  <p><em>DSA Case Study — BSIT 2-2, Polytechnic University of the Philippines – Quezon City</em></p>
  
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white"></a>
  <img alt="Rich TUI" src="https://img.shields.io/badge/TUI-Rich-6f42c1">
  <img alt="NumPy" src="https://img.shields.io/badge/NumPy-Analytics-013243">
  <img alt="Matplotlib" src="https://img.shields.io/badge/Plots-Matplotlib-11557c">
</div>
-

### Overview

This is a Case Study from a Group from BSIT 2-2 in Polytechnic University of the Philippines – Quezon City, for the subject Data Structures & Algorithms.  
The main name of this app is Academic Analytics Lite.

It ingests student CSV data, computes weighted grades, groups by section, surfaces insights (distributions, rankings, hardest quiz), and can export per‑section CSV reports. You can run it as a quick, scripted showcase or explore via an interactive Rich-powered CLI.

### Table of Contents
- Features
- Quickstart
- Usage
- Configuration
- Project Structure
- Data & Outputs
- Complexity Notes
- Contributors

### Features
- Weighted grade computation with configurable weights
- Section grouping and summaries
- Top/Bottom N rankings (overall and per section)
- Grade letter distribution tables
- Quiz insights (hardest topic, cross‑section averages)
- Midterm → Final improvement insights (overall and per‑section)
- Attendance ↔ Grade correlation (overall and per‑section)
- Compare sections (text insights) for each quiz
- Interactive TUI with pagination and menus (Rich)
- CSV exports per section

### Quickstart
1) Create a virtual environment

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

2) Install dependencies

```bash
pip install -r requirements.txt
```

3) Run

```bash
# Showcase (scripted demo)
python main.py

# Interactive CLI
python main.py --cli
```

### Usage
- Showcase prints a curated sequence of tables and insights to the terminal.
- CLI provides menus for:
  - Course Dashboard
    - Overall Roster, Grade Distribution, Section Averages
    - Overall Ranking (Top N), Curve Preview, Histograms
    - Improvement Insights (Midterm→Final)
    - Attendance‑Grade Correlation (Overall)
  - Section Analytics
    - View/Sort Section, Top/Bottom N, Grade Distribution
    - Hardest Topic per Section, Quiz Averages Comparison
    - Compare Sections (Text Insights)
    - Section Improvement Insights
    - Section Attendance Correlation
    - Section Histograms
  - Student Reports (at‑risk list, CSV export, lookup)
  - Tools & Utilities (load/reload data, insert/delete demo student, custom plot)

### Configuration
Edit `config.json` to point to your input and tweak behavior:
- `file_paths.input_csv`: path to the input CSV (e.g., `data/input_bsit.csv`)
- `file_paths.output_dir`: directory for generated reports (e.g., `output/`)
- `grade_weights`: weights for quizzes, midterm, final, attendance
- `thresholds.at_risk_cutoff`: numeric grade below which students are listed as at‑risk
- `thresholds.grade_letters`: cutoffs for A/B/C/D buckets

### Project Structure
- `app/` — application modules (CLI, core, analytics, reporting)
- `data/` — sample input CSV files
- `output/` — generated CSV reports
- `tests/` — unit tests
- `config.json` — runtime configuration
- `main.py` — entry point (showcase by default; `--cli` for interactive)

### Data & Outputs
- Sample inputs are provided under `data/` (e.g., `input_bsit.csv`).
- Exports are written to `output/` as `section_<SECTION>_report.csv`.


### Complexity Notes
`read_csv_data` in `app/core.py` performs a single pass over the CSV using `csv.DictReader`, then iterates each row's fields to strip strings and parse numeric values (with range checks).

- Time: O(R × C), where R is the number of rows and C is the number of columns. Each cell is processed in O(1) average time (strip/parse/check).
- Space: O(R × C) to store the resulting list of row dictionaries. Transient working memory is O(C) per row; overall memory is dominated by the accumulated output.

### Contributors

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/JChristian25">
        <img src="https://github.com/JChristian25.png?size=100" width="90" alt="JChristian25" /><br/>
        <sub><b>John Christian Linaban</b></sub><br/>
        <sub>@JChristian25</sub><br/>
        <sub><i>Full‑stack Programmer</i></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/jeop-qrs">
        <img src="https://github.com/jeop-qrs.png?size=100" width="90" alt="jeop-qrs" /><br/>
        <sub><b>Jeoffrey Isaiah Hernandez</b></sub><br/>
        <sub>@jeop-qrs</sub><br/>
        <sub><i>Backend</i></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/yyxy0">
        <img src="https://github.com/yyxy0.png?size=100" width="90" alt="yyxy0" /><br/>
        <sub><b>Daniel Go Micompal</b></sub><br/>
        <sub>@yyxy0</sub><br/>
        <sub><i>Backend</i></sub>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center">
      <a href="https://github.com/Cursed-10">
        <img src="https://github.com/Cursed-10.png?size=100" width="90" alt="Cursed-10" /><br/>
        <sub><b>Kirsten Licup</b></sub><br/>
        <sub>@Cursed-10</sub><br/>
        <sub><i>Frontend</i></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/marymargaretteviray15-hub">
        <img src="https://github.com/marymargaretteviray15-hub.png?size=100" width="90" alt="marymargaretteviray15-hub" /><br/>
        <sub><b>Mary Margarette Viray</b></sub><br/>
        <sub>@marymargaretteviray15-hub</sub><br/>
        <sub><i>Frontend</i></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/PumpkinDelirious">
        <img src="https://github.com/PumpkinDelirious.png?size=100" width="90" alt="PumpkinDelirious" /><br/>
        <sub><b>John Miles Varca</b></sub><br/>
        <sub>@PumpkinDelirious</sub><br/>
        <sub><i>Backend</i></sub>
      </a>
    </td>
  </tr>
</table>
