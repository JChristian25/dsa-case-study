import numpy as np
from typing import Any, Dict, List, Sequence

def convert_to_numpy(students: List[Dict[str, Any]], score_keys: List[str]) -> np.ndarray:
    n_cols = len(score_keys)
    if not students:
        return np.zeros((0, n_cols), dtype=float)
    rows: List[List[float]] = []
    append_row = rows.append
    sk = list(score_keys)
    for stud in students:
        row: List[float] = []
        rappend = row.append
        sget = stud.get
        for key in sk:
            val = sget(key)
            if val is None:
                rappend(0.0)
            else:
                # Assuming numeric or numeric-like based on dataset contracts
                rappend(float(val))
        append_row(row)
    return np.asarray(rows, dtype=float)


def compute_weighted_grades_numpy(
    students: List[Dict[str, Any]],
    weight_cfg: Dict[str, float],
    score_keys: Sequence[str] = ("quiz1", "quiz2", "quiz3", "quiz4", "quiz5", "midterm", "final", "attendance_percent"),
) -> List[Dict[str, Any]]:
    if not students:
        return []
    # 1) Convert to matrix (None -> 0.0)
    sk = list(score_keys)
    scores = convert_to_numpy(students, sk)

    # 2) Build per-column weight vector matching stats.py semantics
    #    avg(quizzes) * quizzes_total  => distribute quizzes_total across quiz columns
    weights = np.zeros(len(sk), dtype=float)
    quiz_keys = [k for k in sk if k.lower().startswith("quiz")]
    n_quizzes = max(1, len(quiz_keys))
    quiz_share = float(weight_cfg.get("quizzes_total", 0.0)) / n_quizzes
    for idx, key in enumerate(sk):
        lk = key.lower()
        if lk == "midterm":
            weights[idx] = float(weight_cfg.get("midterm", 0.0))
        elif lk == "final":
            weights[idx] = float(weight_cfg.get("final", 0.0))
        elif lk in ("attendance_percent", "attendance", "attendance_percentage"):
            weights[idx] = float(weight_cfg.get("attendance", 0.0))
        elif lk.startswith("quiz"):
            weights[idx] = quiz_share
        else:
            weights[idx] = 0.0

    # 3) Compute grades via dot product, rounded to 2 decimals for parity
    if scores.size == 0:
        grades = np.array([], dtype=float)
    else:
        w = weights.reshape(-1)
        if scores.shape[1] != w.shape[0]:
            raise ValueError(
                f"Mismatched shapes: scores has {scores.shape[1]} columns, weights has {w.shape[0]}"
            )
        grades = np.round(scores @ w, 2)

    # Attach to copies to avoid mutating caller's objects
    out: List[Dict[str, Any]] = []
    for stud, g in zip(students, grades):
        s = stud.copy()
        # g already rounded to 2 decimals above; avoid redundant rounding
        s["weighted_grade"] = float(g)
        out.append(s)
    return out
