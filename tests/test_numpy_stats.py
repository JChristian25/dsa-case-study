"""Tests comparing NumPy-based and pure-Python weighted grade computations.

Authors:
- John Christian Linaban
"""

import numpy as np
import time

from app.analytics.stats import compute_weighted_grades as compute_weighted_grades_py
from app.analytics.numpy_stats import (
	compute_weighted_grades_numpy as compute_weighted_grades_np,
)


def _generate_mock_students(count: int = 2000, seed: int = 42):
	rng = np.random.default_rng(seed)

	p_none_quiz = 0.1
	p_none_exam = 0.12
	p_none_attn = 0.08

	students = []
	sections = ["BSIT-1A", "BSIT-1B", "BSIT 2-1", "BSIT 2-2", "BSIT 2-3"]

	for i in range(count):
		sid = f"2024-{i+1000:04d}"
		sec = sections[i % len(sections)]

		# Base random scores
		quiz_vals = rng.integers(50, 101, size=5).astype(float).tolist()
		midterm = float(rng.integers(50, 101))
		final = float(rng.integers(50, 101))
		attn = float(rng.integers(60, 101))

		# Randomly null some fields
		for q in range(5):
			if rng.random() < p_none_quiz:
				quiz_vals[q] = None
		if rng.random() < p_none_exam:
			midterm = None
		if rng.random() < p_none_exam:
			final = None
		if rng.random() < p_none_attn:
			attn = None

		students.append(
			{
				"student_id": sid,
				"last_name": f"LN{i}",
				"first_name": f"FN{i}",
				"section": sec,
				"quiz1": quiz_vals[0],
				"quiz2": quiz_vals[1],
				"quiz3": quiz_vals[2],
				"quiz4": quiz_vals[3],
				"quiz5": quiz_vals[4],
				"midterm": midterm,
				"final": final,
				"attendance_percent": attn,
			}
		)

	return students


def _mock_students():
	base = [
		{
			'student_id': '2024-0001', 'last_name': 'Doe', 'first_name': 'John', 'section': 'BSIT-1A',
			'quiz1': 85, 'quiz2': 90, 'quiz3': 88, 'quiz4': 92, 'quiz5': 89,
			'midterm': 91, 'final': 93, 'attendance_percent': 95,
		},
		{
			'student_id': '2024-0002', 'last_name': 'Smith', 'first_name': 'Jane', 'section': 'BSIT-1A',
			'quiz1': 75, 'quiz2': None, 'quiz3': 82.5, 'quiz4': 70, 'quiz5': 68,
			'midterm': 73, 'final': 78, 'attendance_percent': None,
		},
		{
			'student_id': '2024-0003', 'last_name': 'Lee', 'first_name': 'Chris', 'section': 'BSIT-1B',
			'quiz1': None, 'quiz2': None, 'quiz3': None, 'quiz4': None, 'quiz5': None,
			'midterm': None, 'final': 60, 'attendance_percent': 80,
		},
	]
	# Add a larger synthetic batch to stress test performance paths
	return base + _generate_mock_students()


def _weights():
	# Typical weighting scheme from the repo
	return {
		'quizzes_total': 0.2,
		'midterm': 0.3,
		'final': 0.4,
		'attendance': 0.1,
	}


def test_numpy_weighted_grades_matches_python_version():
	students = _mock_students()
	weights = _weights()

	# Compute via original Python implementation (time it)
	t0 = time.perf_counter()
	py_result = compute_weighted_grades_py(students, weights)
	t1 = time.perf_counter()

	# Compute via NumPy implementation (time it)
	t2 = time.perf_counter()
	np_result = compute_weighted_grades_np(students, weights)
	t3 = time.perf_counter()

	# Compare weighted_grade per student in order
	assert len(py_result) == len(np_result)
	for p, n in zip(py_result, np_result):
		assert p['student_id'] == n['student_id']
		# Both implementations round to 2 decimals, so exact match expected
		assert p['weighted_grade'] == n['weighted_grade']

	# Record timing information (displayed in test output)
	py_time = t1 - t0
	np_time = t3 - t2
	ratio = py_time / np_time if np_time > 0 else float('inf')
	print(f"Timing -> pure Python: {py_time:.6f}s | NumPy: {np_time:.6f}s | speedup: {ratio:.2f}x")

