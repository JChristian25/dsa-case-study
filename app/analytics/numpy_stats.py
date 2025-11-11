"""NumPy implementation of weighted grades and conversion utilities.

Authors:
- John Christian Linaban
"""

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
    # Convert to matrix (None -> 0.0)
    sk = list(score_keys)
    scores = convert_to_numpy(students, sk)
    if scores.size == 0:
        return [dict(stud, weighted_grade=0.0) for stud in students]

    # Identify column indices
    key_to_idx = {k: i for i, k in enumerate(sk)}
    quiz_idxs = [key_to_idx[k] for k in sk if k.lower().startswith("quiz")]
    mid_idx = key_to_idx.get("midterm")
    fin_idx = key_to_idx.get("final")
    att_idx = key_to_idx.get("attendance_percent")

    # Compute quiz average per row, with prior None->0.0 mapping, then ROUND TO 2 DECIMALS
    # Using NumPy's native rounding for maximum speed
    if len(quiz_idxs) > 0:
        quiz_mat = scores[:, quiz_idxs]
        quiz_mean = np.mean(quiz_mat, axis=1)
        # Use NumPy's native rounding for speed
        quiz_mean = np.round(quiz_mean, 2)
        quiz_component = quiz_mean * float(weight_cfg.get("quizzes_total", 0.0))
    else:
        quiz_component = np.zeros(scores.shape[0], dtype=float)

    # Other weighted components
    mid_component = (scores[:, mid_idx] if mid_idx is not None else 0.0) * float(weight_cfg.get("midterm", 0.0))
    fin_component = (scores[:, fin_idx] if fin_idx is not None else 0.0) * float(weight_cfg.get("final", 0.0))
    att_component = (scores[:, att_idx] if att_idx is not None else 0.0) * float(weight_cfg.get("attendance", 0.0))

    total = quiz_component + mid_component + fin_component + att_component
    # Use NumPy's native rounding for speed
    grades = np.round(total, 2)

    out: List[Dict[str, Any]] = []
    for stud, g in zip(students, grades):
        s = stud.copy()
        s["weighted_grade"] = float(g)
        out.append(s)
    return out
