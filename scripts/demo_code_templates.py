"""
Demo Code Templates for CodeGuard 150-Submission Synthetic Dataset
Provides 30 valid Python implementations for each of the 5 assignments:
- Category A: 10 independent implementations
- Category B: 5 implementations with similar structure but changed identifiers
- Category C: 5 implementations with similar logic and altered syntax
- Category D: 5 intentionally modified or lightly obfuscated copies
- Category E: 5 implementations using different strategies / algorithms
"""

def get_assignment_code(assignment_num: int, variant_idx: int, student_reg: str) -> str:
    """
    Returns valid Python source code for the given assignment (1-5) and variant (0-29).
    variant_idx:
      0-9:   Category A (10 independent)
      10-14: Category B (5 changed identifiers)
      15-19: Category C (5 altered syntax)
      20-24: Category D (5 lightly obfuscated / modified copies)
      25-29: Category E (5 alternative strategies)
    """
    generators = {
        1: _get_ca01_code,
        2: _get_ca02_code,
        3: _get_ca03_code,
        4: _get_ca04_code,
        5: _get_ca05_code,
    }
    gen = generators.get(assignment_num)
    if not gen:
        raise ValueError(f"Unknown assignment number: {assignment_num}")
    return gen(variant_idx, student_reg)


# ==============================================================================
# ASSIGNMENT 1: CA-01: Student Performance Analyzer
# ==============================================================================
_CA01_BASE = '''# Student Performance Analyzer
# Reference Implementation

def calculate_average(scores):
    if not scores:
        return 0.0
    total = sum(scores)
    return round(total / len(scores), 2)

def assign_grade(average):
    if average >= 90.0:
        return 'A'
    elif average >= 80.0:
        return 'B'
    elif average >= 70.0:
        return 'C'
    elif average >= 60.0:
        return 'D'
    else:
        return 'F'

def compute_class_statistics(student_records):
    """Computes mean, highest, and lowest scores for a list of student records."""
    if not student_records:
        return {"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}
    
    all_averages = []
    for student in student_records:
        avg = calculate_average(student.get("scores", []))
        all_averages.append(avg)
        student["average"] = avg
        student["grade"] = assign_grade(avg)
        
    return {
        "count": len(student_records),
        "class_average": round(sum(all_averages) / len(all_averages), 2),
        "highest": max(all_averages),
        "lowest": min(all_averages)
    }

if __name__ == "__main__":
    sample = [
        {"name": "Alice", "scores": [85, 92, 78]},
        {"name": "Bob", "scores": [70, 65, 80]},
        {"name": "Charlie", "scores": [95, 98, 92]}
    ]
    print(compute_class_statistics(sample))
'''

def _get_ca01_code(idx: int, reg: str) -> str:
    # 0..9: Independent implementations
    indep = [
        # 0: OOP with Class
        f'''"""Student Performance Analyzer - OOP Architecture
Registration: {reg}
"""
class StudentRecord:
    def __init__(self, name: str, scores: list):
        self.name = name
        self.scores = [float(s) for s in scores]
        self.average = self._calc_avg()
        self.grade = self._calc_grade()

    def _calc_avg(self) -> float:
        return round(sum(self.scores) / len(self.scores), 2) if self.scores else 0.0

    def _calc_grade(self) -> str:
        if self.average >= 90: return 'A'
        if self.average >= 80: return 'B'
        if self.average >= 70: return 'C'
        if self.average >= 60: return 'D'
        return 'F'

class GradeBook:
    def __init__(self):
        self.records = []

    def add_student(self, name: str, scores: list):
        self.records.append(StudentRecord(name, scores))

    def summarize(self) -> dict:
        if not self.records:
            return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
        avgs = [r.average for r in self.records]
        return {{
            "count": len(self.records),
            "class_average": round(sum(avgs) / len(avgs), 2),
            "highest": max(avgs),
            "lowest": min(avgs)
        }}

if __name__ == "__main__":
    gb = GradeBook()
    gb.add_student("Alex", [88, 91, 79])
    gb.add_student("Beth", [75, 82, 80])
    print(gb.summarize())
''',
        # 1: Functional style with reduce & map
        f'''"""Functional Performance Evaluator
Registration: {reg}
"""
from functools import reduce

def compute_mean(nums):
    return round(reduce(lambda acc, x: acc + x, nums, 0) / len(nums), 2) if nums else 0.0

def determine_letter_grade(val):
    grade_scale = [(90, 'A'), (80, 'B'), (70, 'C'), (60, 'D'), (0, 'F')]
    for cutoff, letter in grade_scale:
        if val >= cutoff:
            return letter
    return 'F'

def process_roster(roster):
    if not roster:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    scored = list(map(lambda item: compute_mean(item.get("scores", [])), roster))
    return {{
        "count": len(roster),
        "class_average": round(sum(scored) / len(scored), 2),
        "highest": max(scored) if scored else 0.0,
        "lowest": min(scored) if scored else 0.0
    }}

if __name__ == "__main__":
    print(process_roster([{{"scores": [90, 85, 92]}}, {{"scores": [60, 70, 75]}}]))
''',
        # 2: Dictionary comprehension & tuple scale
        f'''"""Dictionary accumulator student analyzer
Registration: {reg}
"""
GRADE_BOUNDARIES = ((90.0, 'A'), (80.0, 'B'), (70.0, 'C'), (60.0, 'D'), (0.0, 'F'))

def calculate_student_gpa(marks):
    count = len(marks)
    if count == 0:
        return 0.0, 'F'
    mean = round(sum(marks) / count, 2)
    grade = next(g for bound, g in GRADE_BOUNDARIES if mean >= bound)
    return mean, grade

def build_grade_report(data):
    results = {{}}
    for st_id, scores in data.items():
        avg, gr = calculate_student_gpa(scores)
        results[st_id] = {{"average": avg, "grade": gr}}
    
    averages = [v["average"] for v in results.values()]
    summary = {{
        "count": len(results),
        "class_average": round(sum(averages) / len(averages), 2) if averages else 0.0,
        "highest": max(averages) if averages else 0.0,
        "lowest": min(averages) if averages else 0.0
    }}
    return results, summary
''',
        # 3: Statistics module & custom variance
        f'''"""Statistical Grade Analysis Suite
Registration: {reg}
"""
import math

def analyze_student_scores(records):
    stats = {{"count": len(records), "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    if not records:
        return stats
        
    means = []
    for r in records:
        s = r.get("scores", [])
        m = sum(s) / len(s) if s else 0.0
        means.append(round(m, 2))
        
    stats["class_average"] = round(sum(means) / len(means), 2)
    stats["highest"] = max(means)
    stats["lowest"] = min(means)
    
    # Calculate sample standard deviation
    avg = stats["class_average"]
    variance = sum((x - avg) ** 2 for x in means) / len(means) if len(means) > 1 else 0.0
    stats["std_dev"] = round(math.sqrt(variance), 2)
    return stats
''',
        # 4: Procedural with strict type checking & docstrings
        f'''"""Clean Procedural Student Statistics
Registration: {reg}
"""
from typing import List, Dict, Any

def get_mean_score(scores: List[float]) -> float:
    \"\"\"Return arithmetic mean rounded to 2 decimal places.\"\"\"
    if not scores:
        return 0.0
    return round(float(sum(scores)) / len(scores), 2)

def get_performance_tier(avg: float) -> str:
    \"\"\"Map numeric score to letter grade tier.\"\"\"
    if avg >= 90.0:
        return "Tier-A"
    elif avg >= 80.0:
        return "Tier-B"
    elif avg >= 70.0:
        return "Tier-C"
    elif avg >= 60.0:
        return "Tier-D"
    return "Tier-F"

def evaluate_batch(students: List[Dict[str, Any]]) -> Dict[str, Any]:
    averages = [get_mean_score(s.get("scores", [])) for s in students]
    if not averages:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    return {{
        "count": len(students),
        "class_average": round(sum(averages) / len(averages), 2),
        "highest": max(averages),
        "lowest": min(averages)
    }}
''',
        # 5: Dataclass based approach
        f'''"""Dataclass Grade Analyzer
Registration: {reg}
"""
from dataclasses import dataclass
from typing import List

@dataclass
class ReportCard:
    student_id: str
    scores: List[int]
    
    @property
    def average(self) -> float:
        return round(sum(self.scores) / len(self.scores), 2) if self.scores else 0.0
        
    @property
    def grade(self) -> str:
        a = self.average
        return 'A' if a >= 90 else ('B' if a >= 80 else ('C' if a >= 70 else ('D' if a >= 60 else 'F')))

def compute_batch_summary(cards: List[ReportCard]):
    if not cards:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    vals = [c.average for c in cards]
    return {{
        "count": len(cards),
        "class_average": round(sum(vals) / len(vals), 2),
        "highest": max(vals),
        "lowest": min(vals)
    }}
''',
        # 6: While loop accumulator with percentile calculation
        f'''"""Iterative Student Evaluation
Registration: {reg}
"""
def calc_stats_iterative(dataset):
    idx = 0
    averages = []
    while idx < len(dataset):
        entry = dataset[idx]
        marks = entry.get("scores", [])
        sub_sum = 0
        j = 0
        while j < len(marks):
            sub_sum += marks[j]
            j += 1
        avg = round(sub_sum / len(marks), 2) if marks else 0.0
        averages.append(avg)
        idx += 1
        
    if not averages:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    return {{
        "count": len(dataset),
        "class_average": round(sum(averages) / len(averages), 2),
        "highest": max(averages),
        "lowest": min(averages)
    }}
''',
        # 7: Recursive processing
        f'''"""Recursive Student Aggregator
Registration: {reg}
"""
def rec_sum(arr, n):
    if n <= 0:
        return 0
    return rec_sum(arr, n - 1) + arr[n - 1]

def rec_avg(marks):
    if not marks:
        return 0.0
    return round(rec_sum(marks, len(marks)) / len(marks), 2)

def evaluate_recursively(students):
    if not students:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    averages = [rec_avg(st.get("scores", [])) for st in students]
    return {{
        "count": len(students),
        "class_average": round(sum(averages) / len(averages), 2),
        "highest": max(averages),
        "lowest": min(averages)
    }}
''',
        # 8: Dictionary with letter grade frequencies
        f'''"""Grade Distribution Analyzer
Registration: {reg}
"""
def summarize_class_performance(student_list):
    res = {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0, "distribution": {{'A':0,'B':0,'C':0,'D':0,'F':0}}}}
    if not student_list:
        return res
        
    scores_collected = []
    for s in student_list:
        sc = s.get("scores", [])
        avg = round(sum(sc) / len(sc), 2) if sc else 0.0
        scores_collected.append(avg)
        
        g = 'F'
        if avg >= 90: g = 'A'
        elif avg >= 80: g = 'B'
        elif avg >= 70: g = 'C'
        elif avg >= 60: g = 'D'
        res["distribution"][g] += 1
        
    res["count"] = len(student_list)
    res["class_average"] = round(sum(scores_collected) / len(scores_collected), 2)
    res["highest"] = max(scores_collected)
    res["lowest"] = min(scores_collected)
    return res
''',
        # 9: Weighted exam/quiz performance analyzer
        f'''"""Weighted Score Analyzer
Registration: {reg}
"""
def compute_weighted_average(components: dict) -> float:
    # exams: 50%, assignments: 30%, quizzes: 20%
    e = sum(components.get("exams", [])) / len(components.get("exams", [1]))
    a = sum(components.get("assignments", [])) / len(components.get("assignments", [1]))
    q = sum(components.get("quizzes", [])) / len(components.get("quizzes", [1]))
    return round(e * 0.5 + a * 0.3 + q * 0.2, 2)

def process_weighted_roster(roster):
    if not roster:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    avgs = [compute_weighted_average(r) for r in roster]
    return {{
        "count": len(roster),
        "class_average": round(sum(avgs) / len(avgs), 2),
        "highest": max(avgs),
        "lowest": min(avgs)
    }}
'''
    ]

    if idx < 10:
        return indep[idx]

    # 10..14: Category B: Changed identifiers from base
    if 10 <= idx <= 14:
        v_idx = idx - 10
        id_maps = [
            ("calc_mean", "find_grade", "get_metrics", "marks", "res_list"),
            ("get_avg", "determine_rank", "run_class_summary", "points", "student_pool"),
            ("compute_score_mean", "assign_letter", "aggregate_results", "items", "records_array"),
            ("evaluate_mean", "grade_mapper", "analyze_roster", "raw_vals", "entries"),
            ("average_score", "classify_score", "batch_statistics", "exam_scores", "batch_data")
        ]
        f_avg, f_grd, f_stats, var_scores, var_records = id_maps[v_idx]
        return f'''# Student Performance Analyzer - Variation {v_idx + 1}
# Registration: {reg}

def {f_avg}({var_scores}):
    if not {var_scores}:
        return 0.0
    total_val = sum({var_scores})
    return round(total_val / len({var_scores}), 2)

def {f_grd}(score_val):
    if score_val >= 90.0:
        return 'A'
    elif score_val >= 80.0:
        return 'B'
    elif score_val >= 70.0:
        return 'C'
    elif score_val >= 60.0:
        return 'D'
    else:
        return 'F'

def {f_stats}({var_records}):
    if not {var_records}:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    
    collected_avgs = []
    for item in {var_records}:
        val_avg = {f_avg}(item.get("scores", []))
        collected_avgs.append(val_avg)
        item["average"] = val_avg
        item["grade"] = {f_grd}(val_avg)
        
    return {{
        "count": len({var_records}),
        "class_average": round(sum(collected_avgs) / len(collected_avgs), 2),
        "highest": max(collected_avgs),
        "lowest": min(collected_avgs)
    }}
'''

    # 15..19: Category C: Altered syntax / loop structure
    if 15 <= idx <= 19:
        c_idx = idx - 15
        if c_idx == 0:
            return f'''# Student Performance Analyzer - While loops syntax
# Registration: {reg}

def calculate_average(scores):
    if len(scores) == 0:
        return 0.0
    s, i = 0, 0
    while i < len(scores):
        s += scores[i]
        i += 1
    return round(s / len(scores), 2)

def assign_grade(average):
    return 'A' if average >= 90.0 else ('B' if average >= 80.0 else ('C' if average >= 70.0 else ('D' if average >= 60.0 else 'F')))

def compute_class_statistics(student_records):
    if not student_records:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    
    all_averages = [calculate_average(st.get("scores", [])) for st in student_records]
    for idx, st in enumerate(student_records):
        st["average"] = all_averages[idx]
        st["grade"] = assign_grade(all_averages[idx])
        
    return {{
        "count": len(student_records),
        "class_average": round(sum(all_averages) / len(all_averages), 2),
        "highest": max(all_averages),
        "lowest": min(all_averages)
    }}
'''
        elif c_idx == 1:
            return f'''# Student Performance Analyzer - List comprehensions & ternaries
# Registration: {reg}

def calculate_average(scores):
    return round(sum(scores) / len(scores), 2) if bool(scores) else 0.0

def assign_grade(average):
    thresholds = [(90.0, 'A'), (80.0, 'B'), (70.0, 'C'), (60.0, 'D')]
    for limit, letter in thresholds:
        if average >= limit:
            return letter
    return 'F'

def compute_class_statistics(student_records):
    n = len(student_records)
    if n == 0:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    
    avgs = [calculate_average(s.get("scores", [])) for s in student_records]
    return {{
        "count": n,
        "class_average": round(sum(avgs) / n, 2),
        "highest": max(avgs),
        "lowest": min(avgs)
    }}
'''
        elif c_idx == 2:
            return f'''# Student Performance Analyzer - Explicit accumulator
# Registration: {reg}

def calculate_average(scores):
    acc = 0.0
    for val in scores:
        acc += float(val)
    return round(acc / len(scores), 2) if len(scores) > 0 else 0.0

def assign_grade(average):
    scale = {{'A': average >= 90, 'B': 80 <= average < 90, 'C': 70 <= average < 80, 'D': 60 <= average < 70}}
    for gr, match in scale.items():
        if match:
            return gr
    return 'F'

def compute_class_statistics(student_records):
    if not student_records:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    all_avgs = []
    i = 0
    while i < len(student_records):
        curr = student_records[i]
        val = calculate_average(curr.get("scores", []))
        all_avgs.append(val)
        curr["average"] = val
        curr["grade"] = assign_grade(val)
        i += 1
    return {{
        "count": len(student_records),
        "class_average": round(sum(all_avgs) / len(all_avgs), 2),
        "highest": max(all_avgs),
        "lowest": min(all_avgs)
    }}
'''
        elif c_idx == 3:
            return f'''# Student Performance Analyzer - Generator Expressions
# Registration: {reg}

def calculate_average(scores):
    return round(sum(x for x in scores) / len(scores), 2) if scores else 0.0

def assign_grade(average):
    if average < 60.0:
        return 'F'
    if average < 70.0:
        return 'D'
    if average < 80.0:
        return 'C'
    if average < 90.0:
        return 'B'
    return 'A'

def compute_class_statistics(student_records):
    if not student_records:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    
    all_averages = list(calculate_average(st.get("scores", [])) for st in student_records)
    return {{
        "count": len(student_records),
        "class_average": round(sum(all_averages) / len(all_averages), 2),
        "highest": max(all_averages),
        "lowest": min(all_averages)
    }}
'''
        else:
            return f'''# Student Performance Analyzer - Inverted logic
# Registration: {reg}

def calculate_average(scores):
    if len(scores) != 0:
        return round(float(sum(scores)) / float(len(scores)), 2)
    return 0.0

def assign_grade(average):
    letters = ['F', 'D', 'C', 'B', 'A']
    pts = [0, 60, 70, 80, 90]
    assigned = 'F'
    for i in range(len(pts)):
        if average >= pts[i]:
            assigned = letters[i]
    return assigned

def compute_class_statistics(student_records):
    if len(student_records) == 0:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    res = [calculate_average(rec.get("scores", [])) for rec in student_records]
    return {{
        "count": len(student_records),
        "class_average": round(sum(res) / len(res), 2),
        "highest": max(res),
        "lowest": min(res)
    }}
'''

    # 20..24: Category D: Lightly obfuscated / modified copies
    if 20 <= idx <= 24:
        d_idx = idx - 20
        return f'''# Student Performance Analyzer - Modified Copy {d_idx + 1}
# Registration: {reg}

_UNUSED_FLAG = {d_idx * 10}

def calculate_average(scores):
    _dummy = 0 + _UNUSED_FLAG
    if not scores or len(scores) == 0:
        return 0.0
    total = sum(scores) + 0.0
    result = round(total / len(scores), 2)
    return result

def assign_grade(average):
    temp_score = average * 1.0
    if temp_score >= 90.0:
        return 'A'
    elif temp_score >= 80.0:
        return 'B'
    elif temp_score >= 70.0:
        return 'C'
    elif temp_score >= 60.0:
        return 'D'
    else:
        return 'F'

def compute_class_statistics(student_records):
    """Computes mean, highest, and lowest scores for a list of student records."""
    _check = bool(student_records)
    if not _check:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    
    all_averages = []
    for idx in range(len(student_records)):
        student = student_records[idx]
        avg = calculate_average(student.get("scores", []))
        all_averages.append(avg)
        student["average"] = avg
        student["grade"] = assign_grade(avg)
        
    class_mean = round(sum(all_averages) / len(all_averages), 2)
    return {{
        "count": len(student_records),
        "class_average": class_mean,
        "highest": max(all_averages),
        "lowest": min(all_averages)
    }}
'''

    # 25..29: Category E: Alternative algorithms / strategies
    e_idx = idx - 25
    alt = [
        # E0: NumPy-like pure python matrix
        f'''"""Matrix-style student grade evaluator
Registration: {reg}
"""
def vectorize_eval(students):
    if not students:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    matrix = [s.get("scores", []) for s in students]
    means = [round(sum(row)/len(row), 2) if row else 0.0 for row in matrix]
    return {{
        "count": len(students),
        "class_average": round(sum(means)/len(means), 2),
        "highest": max(means),
        "lowest": min(means),
        "strategy": "vectorized_matrix"
    }}
''',
        # E1: Custom binning & histogram
        f'''"""Histogram Binning Evaluator
Registration: {reg}
"""
def grade_histogram_analysis(records):
    if not records:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    bins = {{"90-100": 0, "80-89": 0, "70-79": 0, "60-69": 0, "0-59": 0}}
    scores = []
    for r in records:
        sc = r.get("scores", [])
        m = round(sum(sc) / len(sc), 2) if sc else 0.0
        scores.append(m)
        if m >= 90: bins["90-100"] += 1
        elif m >= 80: bins["80-89"] += 1
        elif m >= 70: bins["70-79"] += 1
        elif m >= 60: bins["60-69"] += 1
        else: bins["0-59"] += 1
    return {{
        "count": len(records),
        "class_average": round(sum(scores) / len(scores), 2),
        "highest": max(scores),
        "lowest": min(scores),
        "histogram": bins
    }}
''',
        # E2: Cumulative Ranking Algorithm
        f'''"""Rank-Based Student Performance Evaluator
Registration: {reg}
"""
def rank_students(roster):
    if not roster:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    scored = []
    for item in roster:
        pts = item.get("scores", [])
        avg = round(sum(pts) / len(pts), 2) if pts else 0.0
        scored.append((avg, item.get("name", "Unknown")))
    scored.sort(reverse=True)
    avgs = [s[0] for s in scored]
    return {{
        "count": len(roster),
        "class_average": round(sum(avgs) / len(avgs), 2),
        "highest": avgs[0],
        "lowest": avgs[-1],
        "top_student": scored[0][1]
    }}
''',
        # E3: Quantile normalization
        f'''"""Quantile Student Curve Calculator
Registration: {reg}
"""
def apply_quantile_curve(records):
    if not records:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    raw_means = [round(sum(r.get("scores", [])) / len(r.get("scores", [1])), 2) for r in records]
    highest = max(raw_means)
    boost = 100.0 - highest if highest > 0 else 0.0
    curved = [round(m + boost * 0.2, 2) for m in raw_means]
    return {{
        "count": len(records),
        "class_average": round(sum(curved) / len(curved), 2),
        "highest": max(curved),
        "lowest": min(curved),
        "curved": True
    }}
''',
        # E4: Standard deviation outlier detection
        f'''"""Outlier Detection Student Performance
Registration: {reg}
"""
import math

def flag_outliers(dataset):
    if not dataset:
        return {{"count": 0, "class_average": 0.0, "highest": 0.0, "lowest": 0.0}}
    means = [round(sum(d.get("scores", [])) / len(d.get("scores", [1])), 2) for d in dataset]
    c_avg = sum(means) / len(means)
    variance = sum((x - c_avg)**2 for x in means) / len(means)
    sd = math.sqrt(variance)
    underperformers = [m for m in means if m < c_avg - sd]
    return {{
        "count": len(dataset),
        "class_average": round(c_avg, 2),
        "highest": max(means),
        "lowest": min(means),
        "underperformer_count": len(underperformers)
    }}
'''
    ]
    return alt[e_idx]


# ==============================================================================
# ASSIGNMENT 2: CA-02: Search Algorithm Benchmark
# ==============================================================================
_CA02_BASE = '''# Search Algorithm Benchmark
# Reference Implementation

def linear_search(arr, target):
    """Performs linear search returning target index or -1."""
    for idx in range(len(arr)):
        if arr[idx] == target:
            return idx
    return -1

def binary_search(arr, target):
    """Performs iterative binary search on sorted array."""
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

def benchmark_searches(arr, target):
    import time
    sorted_arr = sorted(arr)
    
    t0 = time.perf_counter()
    l_idx = linear_search(arr, target)
    t_linear = time.perf_counter() - t0
    
    t1 = time.perf_counter()
    b_idx = binary_search(sorted_arr, target)
    t_binary = time.perf_counter() - t1
    
    return {
        "target": target,
        "linear_index": l_idx,
        "linear_time_sec": t_linear,
        "binary_index": b_idx,
        "binary_time_sec": t_binary
    }

if __name__ == "__main__":
    data = list(range(1000))
    print(benchmark_searches(data, 750))
'''

def _get_ca02_code(idx: int, reg: str) -> str:
    indep = [
        # 0: Class based benchmark with iteration counts
        f'''"""Search Algorithm Benchmark Suite
Registration: {reg}
"""
class SearchBenchmark:
    @staticmethod
    def linear_scan(dataset, val):
        steps = 0
        for i, item in enumerate(dataset):
            steps += 1
            if item == val:
                return i, steps
        return -1, steps

    @staticmethod
    def binary_scan(dataset, val):
        steps = 0
        left, right = 0, len(dataset) - 1
        while left <= right:
            steps += 1
            pivot = (left + right) // 2
            if dataset[pivot] == val:
                return pivot, steps
            elif dataset[pivot] < val:
                left = pivot + 1
            else:
                right = pivot - 1
        return -1, steps

if __name__ == "__main__":
    nums = sorted([5, 12, 19, 21, 37, 45, 59, 81])
    print(SearchBenchmark.linear_scan(nums, 37))
    print(SearchBenchmark.binary_scan(nums, 37))
''',
        # 1: Recursive binary search vs sentinel linear
        f'''"""Recursive Search Suite
Registration: {reg}
"""
def sentinel_linear_search(data, key):
    n = len(data)
    if n == 0:
        return -1
    last = data[-1]
    if last == key:
        return n - 1
    data[-1] = key
    i = 0
    while data[i] != key:
        i += 1
    data[-1] = last
    return i if i < n - 1 else -1

def recursive_binary_search(data, key, low, high):
    if low > high:
        return -1
    mid = low + (high - low) // 2
    if data[mid] == key:
        return mid
    elif data[mid] > key:
        return recursive_binary_search(data, key, low, mid - 1)
    else:
        return recursive_binary_search(data, key, mid + 1, high)
''',
        # 2: Bisect-based vs generator linear
        f'''"""Bisect Search vs Generator
Registration: {reg}
"""
import bisect

def generator_linear_search(seq, target):
    gen = (i for i, x in enumerate(seq) if x == target)
    return next(gen, -1)

def bisect_search(sorted_seq, target):
    idx = bisect.bisect_left(sorted_seq, target)
    if idx < len(sorted_seq) and sorted_seq[idx] == target:
        return idx
    return -1
''',
        # 3: Benchmarking multiple targets
        f'''"""Multi-Target Search Evaluator
Registration: {reg}
"""
def linear_lookup(collection, item):
    for idx, element in enumerate(collection):
        if element == item:
            return idx
    return -1

def binary_lookup(sorted_collection, item):
    start, end = 0, len(sorted_collection) - 1
    while start <= end:
        center = (start + end) >> 1
        val = sorted_collection[center]
        if val == item:
            return center
        elif val < item:
            start = center + 1
        else:
            end = center - 1
    return -1

def run_batch_eval(data, targets):
    s_data = sorted(data)
    return {{
        t: {{"lin": linear_lookup(data, t), "bin": binary_lookup(s_data, t)}}
        for t in targets
    }}
''',
        # 4: Type-hinted clean procedural
        f'''"""Typed Search Comparison
Registration: {reg}
"""
from typing import List, Tuple

def find_first_occurrence(elements: List[int], query: int) -> int:
    for i in range(len(elements)):
        if elements[i] == query:
            return i
    return -1

def find_in_ordered_list(elements: List[int], query: int) -> int:
    lo, hi = 0, len(elements) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        curr = elements[mid]
        if curr == query:
            return mid
        lo, hi = (mid + 1, hi) if curr < query else (lo, mid - 1)
    return -1
''',
        # 5: Search with timing decorator
        f'''"""Timed Search Algorithms
Registration: {reg}
"""
import time
from functools import wraps

def time_it(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        t0 = time.perf_counter()
        res = func(*args, **kwargs)
        return res, time.perf_counter() - t0
    return wrapper

@time_it
def do_linear(arr, x):
    for i in range(len(arr)):
        if arr[i] == x: return i
    return -1

@time_it
def do_binary(sorted_arr, x):
    l, r = 0, len(sorted_arr) - 1
    while l <= r:
        m = (l + r) // 2
        if sorted_arr[m] == x: return m
        if sorted_arr[m] < x: l = m + 1
        else: r = m - 1
    return -1
''',
        # 6: Two-pointer bidirectional linear scan
        f'''"""Bidirectional Linear & Binary Search
Registration: {reg}
"""
def bidirectional_linear(arr, key):
    left, right = 0, len(arr) - 1
    while left <= right:
        if arr[left] == key:
            return left
        if arr[right] == key:
            return right
        left += 1
        right -= 1
    return -1

def standard_binary(arr, key):
    a, b = 0, len(arr) - 1
    while a <= b:
        c = (a + b) // 2
        if arr[c] == key:
            return c
        a, b = (c + 1, b) if arr[c] < key else (a, c - 1)
    return -1
''',
        # 7: Custom Result object
        f'''"""Structured Search Response
Registration: {reg}
"""
class SearchResult:
    def __init__(self, index, comparisons):
        self.index = index
        self.comparisons = comparisons

def count_linear(arr, target):
    ops = 0
    for idx, v in enumerate(arr):
        ops += 1
        if v == target:
            return SearchResult(idx, ops)
    return SearchResult(-1, ops)

def count_binary(arr, target):
    ops = 0
    l, r = 0, len(arr) - 1
    while l <= r:
        ops += 1
        m = (l + r) // 2
        if arr[m] == target:
            return SearchResult(m, ops)
        l, r = (m + 1, r) if arr[m] < target else (l, m - 1)
    return SearchResult(-1, ops)
''',
        # 8: String-search extension
        f'''"""Polymorphic Search Benchmark
Registration: {reg}
"""
def generic_linear(items, probe):
    for i in range(len(items)):
        if items[i] == probe:
            return i
    return -1

def generic_binary(items, probe):
    first = 0
    last = len(items) - 1
    while first <= last:
        midpoint = (first + last) // 2
        if items[midpoint] == probe:
            return midpoint
        elif probe < items[midpoint]:
            last = midpoint - 1
        else:
            first = midpoint + 1
    return -1
''',
        # 9: Exponential / jump search comparison
        f'''"""Search Benchmark Harness
Registration: {reg}
"""
def basic_linear(lst, val):
    for i, x in enumerate(lst):
        if x == val: return i
    return -1

def basic_binary(lst, val):
    low, high = 0, len(lst) - 1
    while low <= high:
        mid = (low + high) // 2
        if lst[mid] == val: return mid
        elif lst[mid] < val: low = mid + 1
        else: high = mid - 1
    return -1
'''
    ]

    if idx < 10:
        return indep[idx]

    # 10..14: Category B: Changed identifiers
    if 10 <= idx <= 14:
        v_idx = idx - 10
        names = [
            ("seq_search", "half_interval_search", "run_search_test", "data_vec", "needle"),
            ("scan_array", "bisect_scan", "evaluate_algorithms", "num_list", "wanted"),
            ("find_linear", "find_binary", "compare_methods", "values", "search_key"),
            ("linear_finder", "binary_finder", "execute_bench", "input_buf", "goal"),
            ("sequential_search", "logarithmic_search", "performance_check", "element_list", "target_val")
        ]
        fn1, fn2, fn3, var1, var2 = names[v_idx]
        return f'''# Search Algorithm Benchmark - Identifier Variation {v_idx + 1}
# Registration: {reg}

def {fn1}({var1}, {var2}):
    for pos in range(len({var1})):
        if {var1}[pos] == {var2}:
            return pos
    return -1

def {fn2}({var1}, {var2}):
    bottom = 0
    top = len({var1}) - 1
    while bottom <= top:
        center = (bottom + top) // 2
        if {var1}[center] == {var2}:
            return center
        elif {var1}[center] < {var2}:
            bottom = center + 1
        else:
            top = center - 1
    return -1

def {fn3}({var1}, {var2}):
    import time
    ordered = sorted({var1})
    
    start_t0 = time.perf_counter()
    res1 = {fn1}({var1}, {var2})
    elapsed1 = time.perf_counter() - start_t0
    
    start_t1 = time.perf_counter()
    res2 = {fn2}(ordered, {var2})
    elapsed2 = time.perf_counter() - start_t1
    
    return {{
        "target": {var2},
        "linear_index": res1,
        "linear_time_sec": elapsed1,
        "binary_index": res2,
        "binary_time_sec": elapsed2
    }}
'''

    # 15..19: Category C: Altered syntax / loops
    if 15 <= idx <= 19:
        c_idx = idx - 15
        return f'''# Search Algorithm Benchmark - Syntax Transformation {c_idx + 1}
# Registration: {reg}

def linear_search(arr, target):
    i = 0
    while i < len(arr):
        if arr[i] == target:
            return i
        i += 1
    return -1

def binary_search(arr, target):
    l = 0
    r = len(arr) - 1
    while l <= r:
        m = l + (r - l) // 2
        val = arr[m]
        if val == target:
            return m
        l, r = (m + 1, r) if val < target else (l, m - 1)
    return -1

def benchmark_searches(arr, target):
    import time
    s_arr = sorted(arr)
    t0 = time.perf_counter()
    i1 = linear_search(arr, target)
    d1 = time.perf_counter() - t0
    
    t1 = time.perf_counter()
    i2 = binary_search(s_arr, target)
    d2 = time.perf_counter() - t1
    return {{
        "target": target,
        "linear_index": i1,
        "linear_time_sec": d1,
        "binary_index": i2,
        "binary_time_sec": d2
    }}
'''

    # 20..24: Category D: Obfuscated / modified copies
    if 20 <= idx <= 24:
        d_idx = idx - 20
        return f'''# Search Algorithm Benchmark - Modified Copy {d_idx + 1}
# Registration: {reg}

def linear_search(arr, target):
    _unused = {d_idx}
    for idx in range(len(arr)):
        if arr[idx] == target and 1 == 1:
            return idx + 0
    return -1

def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        element = arr[mid]
        if element == target:
            return mid
        elif element < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1

def benchmark_searches(arr, target):
    import time
    sorted_arr = list(sorted(arr))
    
    t0 = time.perf_counter()
    l_idx = linear_search(arr, target)
    t_linear = time.perf_counter() - t0
    
    t1 = time.perf_counter()
    b_idx = binary_search(sorted_arr, target)
    t_binary = time.perf_counter() - t1
    
    return {{
        "target": target,
        "linear_index": l_idx,
        "linear_time_sec": t_linear,
        "binary_index": b_idx,
        "binary_time_sec": t_binary
    }}
'''

    # 25..29: Category E: Alternative algorithms
    e_idx = idx - 25
    alt = [
        # E0: Interpolation Search
        f'''"""Interpolation Search vs Linear
Registration: {reg}
"""
def interpolation_search(arr, x):
    low, high = 0, len(arr) - 1
    while low <= high and arr[low] <= x <= arr[high]:
        if low == high:
            return low if arr[low] == x else -1
        pos = low + int(((float(high - low) / (arr[high] - arr[low])) * (x - arr[low])))
        if arr[pos] == x: return pos
        if arr[pos] < x: low = pos + 1
        else: high = pos - 1
    return -1
''',
        # E1: Jump Search
        f'''"""Jump Search Implementation
Registration: {reg}
"""
import math

def jump_search(arr, x):
    n = len(arr)
    step = int(math.sqrt(n)) if n > 0 else 1
    prev = 0
    while prev < n and arr[min(step, n) - 1] < x:
        prev = step
        step += int(math.sqrt(n))
        if prev >= n: return -1
    while prev < min(step, n):
        if arr[prev] == x: return prev
        prev += 1
    return -1
''',
        # E2: Exponential Search
        f'''"""Exponential Search
Registration: {reg}
"""
def exponential_search(arr, target):
    if not arr: return -1
    if arr[0] == target: return 0
    i = 1
    n = len(arr)
    while i < n and arr[i] <= target:
        i *= 2
    l, r = i // 2, min(i, n - 1)
    while l <= r:
        m = (l + r) // 2
        if arr[m] == target: return m
        elif arr[m] < target: l = m + 1
        else: r = m - 1
    return -1
''',
        # E3: Ternary Search
        f'''"""Ternary Search
Registration: {reg}
"""
def ternary_search(arr, key):
    l, r = 0, len(arr) - 1
    while l <= r:
        mid1 = l + (r - l) // 3
        mid2 = r - (r - l) // 3
        if arr[mid1] == key: return mid1
        if arr[mid2] == key: return mid2
        if key < arr[mid1]: r = mid1 - 1
        elif key > arr[mid2]: l = mid2 + 1
        else:
            l = mid1 + 1
            r = mid2 - 1
    return -1
''',
        # E4: Hash Map Lookup Benchmark
        f'''"""Hash Index Lookup vs Linear Scan
Registration: {reg}
"""
def hash_lookup(arr, target):
    index_map = {{val: i for i, val in enumerate(arr)}}
    return index_map.get(target, -1)
'''
    ]
    return alt[e_idx]


# ==============================================================================
# ASSIGNMENT 3: CA-03: Sorting Algorithm Suite
# ==============================================================================
_CA03_BASE = '''# Sorting Algorithm Suite
# Reference Implementation

def bubble_sort(arr):
    data = list(arr)
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j] > data[j + 1]:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data

def insertion_sort(arr):
    data = list(arr)
    for i in range(1, len(data)):
        key = data[i]
        j = i - 1
        while j >= 0 and data[j] > key:
            data[j + 1] = data[j]
            j -= 1
        data[j + 1] = key
    return data

def selection_sort(arr):
    data = list(arr)
    n = len(data)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if data[j] < data[min_idx]:
                min_idx = j
        data[i], data[min_idx] = data[min_idx], data[i]
    return data

if __name__ == "__main__":
    nums = [64, 34, 25, 12, 22, 11, 90]
    print("Bubble:", bubble_sort(nums))
    print("Insertion:", insertion_sort(nums))
    print("Selection:", selection_sort(nums))
'''

def _get_ca03_code(idx: int, reg: str) -> str:
    indep = [
        # 0: Class based sorter suite with swap metrics
        f'''"""Object-Oriented Sorting Suite
Registration: {reg}
"""
class Sorter:
    def __init__(self, dataset):
        self.dataset = list(dataset)

    def bubble(self):
        a = list(self.dataset)
        swaps = 0
        for i in range(len(a)):
            for j in range(len(a) - 1 - i):
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]
                    swaps += 1
        return a, swaps

    def insertion(self):
        a = list(self.dataset)
        for i in range(1, len(a)):
            curr = a[i]
            k = i - 1
            while k >= 0 and a[k] > curr:
                a[k + 1] = a[k]
                k -= 1
            a[k + 1] = curr
        return a

    def selection(self):
        a = list(self.dataset)
        for i in range(len(a)):
            sm = i
            for j in range(i + 1, len(a)):
                if a[j] < a[sm]: sm = j
            a[i], a[sm] = a[sm], a[i]
        return a
''',
        # 1: Early-exit bubble sort and pop-based insertion
        f'''"""Optimized Procedural Sorting
Registration: {reg}
"""
def smart_bubble_sort(arr):
    items = arr[:]
    n = len(items)
    for i in range(n):
        swapped = False
        for j in range(n - 1 - i):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
                swapped = True
        if not swapped:
            break
    return items

def shift_insertion_sort(arr):
    res = []
    for val in arr:
        inserted = False
        for idx in range(len(res)):
            if val < res[idx]:
                res.insert(idx, val)
                inserted = True
                break
        if not inserted:
            res.append(val)
    return res

def scan_selection_sort(arr):
    out = arr[:]
    sz = len(out)
    for step in range(sz):
        best = step
        for probe in range(step + 1, sz):
            if out[probe] < out[best]:
                best = probe
        out[step], out[best] = out[best], out[step]
    return out
''',
        # 2: In-place mutators
        f'''"""In-Place Mutation Sorters
Registration: {reg}
"""
def mutate_bubble(lst):
    l = len(lst)
    for pass_num in range(l - 1, 0, -1):
        for i in range(pass_num):
            if lst[i] > lst[i + 1]:
                temp = lst[i]
                lst[i] = lst[i + 1]
                lst[i + 1] = temp

def mutate_insertion(lst):
    for index in range(1, len(lst)):
        val = lst[index]
        pos = index
        while pos > 0 and lst[pos - 1] > val:
            lst[pos] = lst[pos - 1]
            pos -= 1
        lst[pos] = val

def mutate_selection(lst):
    for fill in range(len(lst) - 1, 0, -1):
        max_pos = 0
        for loc in range(1, fill + 1):
            if lst[loc] > lst[max_pos]:
                max_pos = loc
        lst[fill], lst[max_pos] = lst[max_pos], lst[fill]
''',
        # 3: Bidirectional selection (cocktail style)
        f'''"""Cocktail & Min-Max Sorting
Registration: {reg}
"""
def cocktail_sort(arr):
    a = list(arr)
    n = len(a)
    start, end = 0, n - 1
    while start < end:
        for i in range(start, end):
            if a[i] > a[i + 1]: a[i], a[i + 1] = a[i + 1], a[i]
        end -= 1
        for i in range(end - 1, start - 1, -1):
            if a[i] > a[i + 1]: a[i], a[i + 1] = a[i + 1], a[i]
        start += 1
    return a

def standard_insert(arr):
    res = list(arr)
    for i in range(1, len(res)):
        x = res[i]
        j = i - 1
        while j >= 0 and res[j] > x:
            res[j + 1] = res[j]
            j -= 1
        res[j + 1] = x
    return res

def standard_select(arr):
    res = list(arr)
    for i in range(len(res)):
        m = i
        for j in range(i + 1, len(res)):
            if res[j] < res[m]: m = j
        res[i], res[m] = res[m], res[i]
    return res
''',
        # 4: Generator yielding passes
        f'''"""Step-by-Step Sorting Tracing
Registration: {reg}
"""
def trace_bubble(arr):
    curr = list(arr)
    steps = [list(curr)]
    for i in range(len(curr)):
        for j in range(len(curr) - i - 1):
            if curr[j] > curr[j + 1]:
                curr[j], curr[j + 1] = curr[j + 1], curr[j]
        steps.append(list(curr))
    return steps[-1]

def trace_insertion(arr):
    curr = list(arr)
    for i in range(1, len(curr)):
        k = curr[i]
        j = i - 1
        while j >= 0 and curr[j] > k:
            curr[j + 1] = curr[j]
            j -= 1
        curr[j + 1] = k
    return curr

def trace_selection(arr):
    curr = list(arr)
    for i in range(len(curr)):
        idx = i
        for j in range(i + 1, len(curr)):
            if curr[j] < curr[idx]: idx = j
        curr[i], curr[idx] = curr[idx], curr[i]
    return curr
''',
        # 5: Typed clean implementation
        f'''"""Strictly Typed Sort Suite
Registration: {reg}
"""
from typing import List

def run_bubble(values: List[float]) -> List[float]:
    v = values.copy()
    size = len(v)
    for a in range(size):
        for b in range(size - a - 1):
            if v[b] > v[b + 1]:
                v[b], v[b + 1] = v[b + 1], v[b]
    return v

def run_insertion(values: List[float]) -> List[float]:
    v = values.copy()
    for i in range(1, len(v)):
        elem = v[i]
        p = i - 1
        while p >= 0 and v[p] > elem:
            v[p + 1] = v[p]
            p -= 1
        v[p + 1] = elem
    return v

def run_selection(values: List[float]) -> List[float]:
    v = values.copy()
    n = len(v)
    for i in range(n):
        min_pos = i
        for j in range(i + 1, n):
            if v[j] < v[min_pos]:
                min_pos = j
        v[i], v[min_pos] = v[min_pos], v[i]
    return v
''',
        # 6: Recursive insertion sort
        f'''"""Recursive & Iterative Sorting
Registration: {reg}
"""
def recursive_insertion(arr, n=None):
    if n is None: n = len(arr)
    if n <= 1: return arr
    recursive_insertion(arr, n - 1)
    last = arr[n - 1]
    j = n - 2
    while j >= 0 and arr[j] > last:
        arr[j + 1] = arr[j]
        j -= 1
    arr[j + 1] = last
    return arr

def basic_bubble(arr):
    a = list(arr)
    for i in range(len(a)):
        for j in range(len(a) - 1):
            if a[j] > a[j + 1]: a[j], a[j + 1] = a[j + 1], a[j]
    return a

def basic_select(arr):
    a = list(arr)
    for i in range(len(a)):
        m = i
        for j in range(i + 1, len(a)):
            if a[j] < a[m]: m = j
        a[i], a[m] = a[m], a[i]
    return a
''',
        # 7: While-loop driven implementation
        f'''"""While Loop Sorting Implementations
Registration: {reg}
"""
def while_bubble(arr):
    res = list(arr)
    i = 0
    while i < len(res):
        j = 0
        while j < len(res) - 1 - i:
            if res[j] > res[j + 1]:
                res[j], res[j + 1] = res[j + 1], res[j]
            j += 1
        i += 1
    return res

def while_insertion(arr):
    res = list(arr)
    i = 1
    while i < len(res):
        key = res[i]
        j = i - 1
        while j >= 0 and res[j] > key:
            res[j + 1] = res[j]
            j -= 1
        res[j + 1] = key
        i += 1
    return res

def while_selection(arr):
    res = list(arr)
    i = 0
    while i < len(res):
        min_i = i
        j = i + 1
        while j < len(res):
            if res[j] < res[min_i]: min_i = j
            j += 1
        res[i], res[min_i] = res[min_i], res[i]
        i += 1
    return res
''',
        # 8: Sorting comparison harness
        f'''"""Comparative Sorter Harness
Registration: {reg}
"""
def do_bubble(seq):
    s = list(seq)
    for i in range(len(s)):
        for j in range(len(s) - i - 1):
            if s[j] > s[j + 1]: s[j], s[j + 1] = s[j + 1], s[j]
    return s

def do_insertion(seq):
    s = list(seq)
    for i in range(1, len(s)):
        k = s[i]
        j = i - 1
        while j >= 0 and s[j] > k:
            s[j + 1] = s[j]
            j -= 1
        s[j + 1] = k
    return s

def do_selection(seq):
    s = list(seq)
    for i in range(len(s)):
        m = i
        for j in range(i + 1, len(s)):
            if s[j] < s[m]: m = j
        s[i], s[m] = s[m], s[i]
    return s
''',
        # 9: Binary insertion sort
        f'''"""Binary Insertion and Sorters
Registration: {reg}
"""
import bisect

def binary_insertion_sort(arr):
    res = []
    for item in arr:
        bisect.insort(res, item)
    return res

def classic_bubble(arr):
    a = arr[:]
    for i in range(len(a)):
        for j in range(len(a) - 1 - i):
            if a[j] > a[j + 1]: a[j], a[j + 1] = a[j + 1], a[j]
    return a

def classic_selection(arr):
    a = arr[:]
    for i in range(len(a)):
        low = i
        for j in range(i + 1, len(a)):
            if a[j] < a[low]: low = j
        a[i], a[low] = a[low], a[i]
    return a
'''
    ]

    if idx < 10:
        return indep[idx]

    # 10..14: Category B: Changed identifiers
    if 10 <= idx <= 14:
        v_idx = idx - 10
        fn_tuples = [
            ("b_sort", "i_sort", "s_sort", "input_vec", "pivot_key"),
            ("run_bubble_pass", "run_insertion_pass", "run_selection_pass", "raw_array", "temp_k"),
            ("perform_bubble", "perform_insertion", "perform_selection", "number_list", "key_item"),
            ("sort_bubble_alg", "sort_insert_alg", "sort_select_alg", "elements", "inserted_val"),
            ("bubble_routine", "insertion_routine", "selection_routine", "source_items", "curr_key")
        ]
        b_fn, i_fn, s_fn, v_in, v_key = fn_tuples[v_idx]
        return f'''# Sorting Algorithm Suite - Identifier Variation {v_idx + 1}
# Registration: {reg}

def {b_fn}({v_in}):
    data_copy = list({v_in})
    length = len(data_copy)
    for pass_i in range(length):
        for pass_j in range(0, length - pass_i - 1):
            if data_copy[pass_j] > data_copy[pass_j + 1]:
                data_copy[pass_j], data_copy[pass_j + 1] = data_copy[pass_j + 1], data_copy[pass_j]
    return data_copy

def {i_fn}({v_in}):
    data_copy = list({v_in})
    for step_i in range(1, len(data_copy)):
        {v_key} = data_copy[step_i]
        pos_j = step_i - 1
        while pos_j >= 0 and data_copy[pos_j] > {v_key}:
            data_copy[pos_j + 1] = data_copy[pos_j]
            pos_j -= 1
        data_copy[pos_j + 1] = {v_key}
    return data_copy

def {s_fn}({v_in}):
    data_copy = list({v_in})
    length = len(data_copy)
    for step_i in range(length):
        lowest_pos = step_i
        for step_j in range(step_i + 1, length):
            if data_copy[step_j] < data_copy[lowest_pos]:
                lowest_pos = step_j
        data_copy[step_i], data_copy[lowest_pos] = data_copy[lowest_pos], data_copy[step_i]
    return data_copy
'''

    # 15..19: Category C: Altered syntax
    if 15 <= idx <= 19:
        c_idx = idx - 15
        return f'''# Sorting Algorithm Suite - Syntax Variant {c_idx + 1}
# Registration: {reg}

def bubble_sort(arr):
    res = [x for x in arr]
    n = len(res)
    swapped = True
    while swapped:
        swapped = False
        for i in range(n - 1):
            if res[i] > res[i + 1]:
                res[i], res[i + 1] = res[i + 1], res[i]
                swapped = True
        n -= 1
    return res

def insertion_sort(arr):
    res = [x for x in arr]
    idx = 1
    while idx < len(res):
        key = res[idx]
        j = idx - 1
        while j >= 0 and res[j] > key:
            res[j + 1] = res[j]
            j -= 1
        res[j + 1] = key
        idx += 1
    return res

def selection_sort(arr):
    res = [x for x in arr]
    for i in range(len(res)):
        m = min(range(i, len(res)), key=lambda k: res[k])
        res[i], res[m] = res[m], res[i]
    return res
'''

    # 20..24: Category D: Obfuscated / modified copies
    if 20 <= idx <= 24:
        d_idx = idx - 20
        return f'''# Sorting Algorithm Suite - Modified Copy {d_idx + 1}
# Registration: {reg}

def bubble_sort(arr):
    data = list(arr)
    _dummy = {d_idx} * 2
    n = len(data)
    for i in range(n):
        for j in range(0, n - i - 1):
            if data[j + 1] < data[j] and True:
                data[j], data[j + 1] = data[j + 1], data[j]
    return data

def insertion_sort(arr):
    data = list(arr)
    for i in range(1, len(data)):
        key = data[i]
        j = i - 1
        while j >= 0 and data[j] > key:
            data[j + 1] = data[j]
            j = j - 1
        data[j + 1] = key
    return data

def selection_sort(arr):
    data = list(arr)
    n = len(data)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if data[j] < data[min_idx]:
                min_idx = j
        if min_idx != i:
            data[i], data[min_idx] = data[min_idx], data[i]
    return data
'''

    # 25..29: Category E: Alternative sorting algorithms
    e_idx = idx - 25
    alt = [
        # E0: Quicksort
        f'''"""QuickSort Implementation
Registration: {reg}
"""
def quicksort(arr):
    if len(arr) <= 1: return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
''',
        # E1: Merge Sort
        f'''"""MergeSort Implementation
Registration: {reg}
"""
def mergesort(arr):
    if len(arr) <= 1: return arr
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    res, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            res.append(left[i]); i += 1
        else:
            res.append(right[j]); j += 1
    res.extend(left[i:])
    res.extend(right[j:])
    return res
''',
        # E2: Counting Sort
        f'''"""Counting Sort for Integers
Registration: {reg}
"""
def counting_sort(arr):
    if not arr: return []
    min_val, max_val = min(arr), max(arr)
    count = [0] * (max_val - min_val + 1)
    for x in arr: count[x - min_val] += 1
    res = []
    for i, c in enumerate(count):
        res.extend([i + min_val] * c)
    return res
''',
        # E3: Shell Sort
        f'''"""Shell Sort Implementation
Registration: {reg}
"""
def shell_sort(arr):
    res = list(arr)
    n = len(res)
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            temp = res[i]
            j = i
            while j >= gap and res[j - gap] > temp:
                res[j] = res[j - gap]
                j -= gap
            res[j] = temp
        gap //= 2
    return res
''',
        # E4: Built-in Timsort wrapper
        f'''"""Python Native Timsort Wrapper
Registration: {reg}
"""
def timsort_wrapper(arr):
    return sorted(arr)
'''
    ]
    return alt[e_idx]


# ==============================================================================
# ASSIGNMENT 4: CA-04: Financial Transaction Validator
# ==============================================================================
_CA04_BASE = '''# Financial Transaction Validator
# Reference Implementation

def validate_transaction(tx):
    """Validates individual transaction record."""
    if not isinstance(tx, dict):
        return False, "Invalid record format"
    if "tx_id" not in tx or "amount" not in tx or "type" not in tx:
        return False, "Missing mandatory fields"
    if not isinstance(tx["amount"], (int, float)) or tx["amount"] <= 0:
        return False, "Amount must be positive number"
    if tx["type"] not in ("credit", "debit"):
        return False, "Transaction type must be 'credit' or 'debit'"
    return True, "Valid"

def process_ledger(initial_balance, transactions):
    """Processes a list of transactions against an initial balance."""
    current_balance = float(initial_balance)
    valid_count = 0
    rejected_count = 0
    audit_log = []
    
    for tx in transactions:
        is_valid, msg = validate_transaction(tx)
        if not is_valid:
            rejected_count += 1
            audit_log.append({"tx_id": tx.get("tx_id", "UNKNOWN"), "status": "REJECTED", "reason": msg})
            continue
            
        amt = float(tx["amount"])
        if tx["type"] == "debit":
            if current_balance < amt:
                rejected_count += 1
                audit_log.append({"tx_id": tx["tx_id"], "status": "REJECTED", "reason": "Insufficient funds"})
                continue
            current_balance -= amt
        else:
            current_balance += amt
            
        valid_count += 1
        audit_log.append({"tx_id": tx["tx_id"], "status": "ACCEPTED", "balance_after": round(current_balance, 2)})
        
    return {
        "initial_balance": initial_balance,
        "final_balance": round(current_balance, 2),
        "valid_transactions": valid_count,
        "rejected_transactions": rejected_count,
        "audit_log": audit_log
    }

if __name__ == "__main__":
    sample_txs = [
        {"tx_id": "TX101", "type": "credit", "amount": 500.0},
        {"tx_id": "TX102", "type": "debit", "amount": 200.0},
        {"tx_id": "TX103", "type": "debit", "amount": 1000.0}
    ]
    print(process_ledger(100.0, sample_txs))
'''

def _get_ca04_code(idx: int, reg: str) -> str:
    indep = [
        # 0: OOP BankAccount
        f'''"""OOP Financial Ledger Processor
Registration: {reg}
"""
class BankAccount:
    def __init__(self, balance: float):
        self.balance = float(balance)
        self.accepted = 0
        self.rejected = 0

    def apply_tx(self, tx: dict) -> bool:
        if not isinstance(tx, dict) or "amount" not in tx or "type" not in tx:
            self.rejected += 1
            return False
        amt = tx["amount"]
        if amt <= 0 or tx["type"] not in ("credit", "debit"):
            self.rejected += 1
            return False
        if tx["type"] == "debit" and self.balance < amt:
            self.rejected += 1
            return False
        self.balance += amt if tx["type"] == "credit" else -amt
        self.accepted += 1
        return True

def run_ledger(initial: float, txs: list) -> dict:
    acc = BankAccount(initial)
    for t in txs: acc.apply_tx(t)
    return {{
        "initial_balance": initial,
        "final_balance": round(acc.balance, 2),
        "valid_transactions": acc.accepted,
        "rejected_transactions": acc.rejected
    }}
''',
        # 1: Pure functional stream validator
        f'''"""Functional Ledger Validator
Registration: {reg}
"""
def is_sanitary(tx):
    return isinstance(tx, dict) and tx.get("amount", 0) > 0 and tx.get("type") in ("credit", "debit")

def fold_ledger(balance, tx):
    amt = tx["amount"]
    return balance + amt if tx["type"] == "credit" else balance - amt

def evaluate_stream(start_bal, transactions):
    valid, rejected = 0, 0
    bal = float(start_bal)
    for t in transactions:
        if not is_sanitary(t) or (t["type"] == "debit" and bal < t["amount"]):
            rejected += 1
        else:
            bal = fold_ledger(bal, t)
            valid += 1
    return {{"initial": start_bal, "final": round(bal, 2), "valid": valid, "rejected": rejected}}
''',
        # 2: Schema-dict validation
        f'''"""Schema Rule Transaction Engine
Registration: {reg}
"""
RULES = [
    lambda t: isinstance(t, dict),
    lambda t: "amount" in t and isinstance(t["amount"], (int, float)) and t["amount"] > 0,
    lambda t: t.get("type") in ("credit", "debit")
]

def check_rules(tx):
    return all(r(tx) for r in RULES)

def execute_batch(init_funds, tx_batch):
    funds = float(init_funds)
    ok, fail = 0, 0
    for entry in tx_batch:
        if check_rules(entry):
            diff = entry["amount"] if entry["type"] == "credit" else -entry["amount"]
            if funds + diff >= 0:
                funds += diff
                ok += 1
                continue
        fail += 1
    return {{"initial_balance": init_funds, "final_balance": round(funds, 2), "valid": ok, "rejected": fail}}
''',
        # 3: Dataclass ledger
        f'''"""Dataclass Transaction Accounting
Registration: {reg}
"""
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Transaction:
    tx_id: str
    kind: str
    amount: float
    
    @classmethod
    def from_dict(cls, d: dict) -> Optional['Transaction']:
        if not isinstance(d, dict) or d.get("amount", 0) <= 0 or d.get("type") not in ("credit", "debit"):
            return None
        return cls(str(d.get("tx_id", "")), d["type"], float(d["amount"]))

def process_typed_ledger(start: float, raw_list: List[dict]):
    b = float(start)
    v, r = 0, 0
    for raw in raw_list:
        tx = Transaction.from_dict(raw)
        if tx and (tx.kind == "credit" or b >= tx.amount):
            b += tx.amount if tx.kind == "credit" else -tx.amount
            v += 1
        else:
            r += 1
    return {{"initial": start, "final": round(b, 2), "valid": v, "rejected": r}}
''',
        # 4: Double entry ledger style
        f'''"""Double Entry Validator
Registration: {reg}
"""
def validate_entry(entry):
    if not isinstance(entry, dict): return False
    amt = entry.get("amount", 0)
    t = entry.get("type")
    return amt > 0 and t in ("credit", "debit")

def run_accounting(base_val, entries):
    curr = base_val
    passed, stopped = 0, 0
    for e in entries:
        if validate_entry(e):
            val = e["amount"]
            if e["type"] == "credit":
                curr += val
                passed += 1
            elif curr >= val:
                curr -= val
                passed += 1
            else:
                stopped += 1
        else:
            stopped += 1
    return {{"initial_balance": base_val, "final_balance": round(curr, 2), "valid": passed, "rejected": stopped}}
''',
        # 5: Exception driven validation
        f'''"""Exception Driven Ledger Validation
Registration: {reg}
"""
class InvalidTxError(Exception): pass
class OverdraftError(Exception): pass

def apply_safely(balance, tx):
    if not isinstance(tx, dict) or tx.get("amount", 0) <= 0 or tx.get("type") not in ("credit", "debit"):
        raise InvalidTxError()
    amt = tx["amount"]
    if tx["type"] == "debit" and balance < amt:
        raise OverdraftError()
    return balance + amt if tx["type"] == "credit" else balance - amt

def process_safely(init_b, txs):
    b = init_b
    ok, err = 0, 0
    for t in txs:
        try:
            b = apply_safely(b, t)
            ok += 1
        except (InvalidTxError, OverdraftError):
            err += 1
    return {{"initial_balance": init_b, "final_balance": round(b, 2), "valid": ok, "rejected": err}}
''',
        # 6: Audit trail dict processor
        f'''"""Audit Trail Financial Engine
Registration: {reg}
"""
def process_audit_trail(capital, sequence):
    b = capital
    good, bad = 0, 0
    history = []
    for item in sequence:
        valid = isinstance(item, dict) and item.get("amount", 0) > 0 and item.get("type") in ("credit", "debit")
        if valid and not (item["type"] == "debit" and b < item["amount"]):
            b += item["amount"] if item["type"] == "credit" else -item["amount"]
            good += 1
            history.append((item.get("tx_id"), "OK", b))
        else:
            bad += 1
            history.append((item.get("tx_id"), "ERR", b))
    return {{"initial_balance": capital, "final_balance": round(b, 2), "valid": good, "rejected": bad}}
''',
        # 7: While loop ledger
        f'''"""Iterative Ledger Processor
Registration: {reg}
"""
def while_ledger_processor(starting_sum, ops):
    acc = starting_sum
    success, failure = 0, 0
    idx = 0
    while idx < len(ops):
        curr = ops[idx]
        if isinstance(curr, dict) and curr.get("amount", 0) > 0 and curr.get("type") in ("credit", "debit"):
            if curr["type"] == "credit":
                acc += curr["amount"]
                success += 1
            elif acc >= curr["amount"]:
                acc -= curr["amount"]
                success += 1
            else:
                failure += 1
        else:
            failure += 1
        idx += 1
    return {{"initial_balance": starting_sum, "final_balance": round(acc, 2), "valid": success, "rejected": failure}}
''',
        # 8: Currency and fee model
        f'''"""Transaction Processor with Flat Fee
Registration: {reg}
"""
FEE = 0.50

def run_fee_ledger(opening_bal, tx_records):
    bal = opening_bal
    pass_cnt, drop_cnt = 0, 0
    for r in tx_records:
        if isinstance(r, dict) and r.get("amount", 0) > 0 and r.get("type") in ("credit", "debit"):
            a = r["amount"]
            cost = a if r["type"] == "credit" else a + FEE
            if r["type"] == "credit":
                bal += a
                pass_cnt += 1
            elif bal >= cost:
                bal -= cost
                pass_cnt += 1
            else:
                drop_cnt += 1
        else:
            drop_cnt += 1
    return {{"initial_balance": opening_bal, "final_balance": round(bal, 2), "valid": pass_cnt, "rejected": drop_cnt}}
''',
        # 9: Generator based validator
        f'''"""Generator Ledger Engine
Registration: {reg}
"""
def sanitize_tx_stream(stream):
    for item in stream:
        if isinstance(item, dict) and item.get("amount", 0) > 0 and item.get("type") in ("credit", "debit"):
            yield item, True
        else:
            yield item, False

def execute_stream(init_amt, stream):
    bal = init_amt
    v, r = 0, 0
    for tx, ok in sanitize_tx_stream(stream):
        if ok and not (tx["type"] == "debit" and bal < tx["amount"]):
            bal += tx["amount"] if tx["type"] == "credit" else -tx["amount"]
            v += 1
        else:
            r += 1
    return {{"initial_balance": init_amt, "final_balance": round(bal, 2), "valid": v, "rejected": r}}
'''
    ]

    if idx < 10:
        return indep[idx]

    # 10..14: Category B: Changed identifiers
    if 10 <= idx <= 14:
        v_idx = idx - 10
        names = [
            ("check_tx", "compute_ledger", "tx_item", "start_funds", "running_bal"),
            ("verify_payment", "settle_account", "payment_record", "opening_funds", "net_balance"),
            ("validate_entry", "run_ledger_ops", "entry_dict", "base_balance", "acc_total"),
            ("audit_transaction", "process_book", "trans_obj", "inflow_balance", "state_balance"),
            ("inspect_record", "execute_ledger", "record_map", "initial_capital", "active_balance")
        ]
        fn1, fn2, var_tx, var_init, var_curr = names[v_idx]
        return f'''# Financial Transaction Validator - Identifier Variant {v_idx + 1}
# Registration: {reg}

def {fn1}({var_tx}):
    if not isinstance({var_tx}, dict):
        return False, "Invalid record format"
    if "tx_id" not in {var_tx} or "amount" not in {var_tx} or "type" not in {var_tx}:
        return False, "Missing mandatory fields"
    if not isinstance({var_tx}["amount"], (int, float)) or {var_tx}["amount"] <= 0:
        return False, "Amount must be positive number"
    if {var_tx}["type"] not in ("credit", "debit"):
        return False, "Transaction type must be 'credit' or 'debit'"
    return True, "Valid"

def {fn2}({var_init}, trans_list):
    {var_curr} = float({var_init})
    accepted_records = 0
    rejected_records = 0
    log_output = []
    
    for item in trans_list:
        is_ok, err_desc = {fn1}(item)
        if not is_ok:
            rejected_records += 1
            log_output.append({{"tx_id": item.get("tx_id", "UNKNOWN"), "status": "REJECTED", "reason": err_desc}})
            continue
            
        value = float(item["amount"])
        if item["type"] == "debit":
            if {var_curr} < value:
                rejected_records += 1
                log_output.append({{"tx_id": item["tx_id"], "status": "REJECTED", "reason": "Insufficient funds"}})
                continue
            {var_curr} -= value
        else:
            {var_curr} += value
            
        accepted_records += 1
        log_output.append({{"tx_id": item["tx_id"], "status": "ACCEPTED", "balance_after": round({var_curr}, 2)}})
        
    return {{
        "initial_balance": {var_init},
        "final_balance": round({var_curr}, 2),
        "valid_transactions": accepted_records,
        "rejected_transactions": rejected_records,
        "audit_log": log_output
    }}
'''

    # 15..19: Category C: Altered syntax
    if 15 <= idx <= 19:
        c_idx = idx - 15
        return f'''# Financial Transaction Validator - Syntax Variant {c_idx + 1}
# Registration: {reg}

def validate_transaction(tx):
    valid = isinstance(tx, dict) and "amount" in tx and "type" in tx and tx.get("amount", 0) > 0 and tx.get("type") in ("credit", "debit")
    return (True, "Valid") if valid else (False, "Invalid transaction")

def process_ledger(initial_balance, transactions):
    bal = float(initial_balance)
    ok_count, err_count = 0, 0
    log = []
    
    i = 0
    while i < len(transactions):
        tx = transactions[i]
        ok, msg = validate_transaction(tx)
        if not ok:
            err_count += 1
            log.append({{"tx_id": tx.get("tx_id", ""), "status": "REJECTED"}})
        else:
            amt = float(tx["amount"])
            if tx["type"] == "credit":
                bal += amt
                ok_count += 1
                log.append({{"tx_id": tx.get("tx_id", ""), "status": "ACCEPTED", "balance": round(bal, 2)}})
            elif bal >= amt:
                bal -= amt
                ok_count += 1
                log.append({{"tx_id": tx.get("tx_id", ""), "status": "ACCEPTED", "balance": round(bal, 2)}})
            else:
                err_count += 1
                log.append({{"tx_id": tx.get("tx_id", ""), "status": "REJECTED", "reason": "Low balance"}})
        i += 1
        
    return {{
        "initial_balance": initial_balance,
        "final_balance": round(bal, 2),
        "valid_transactions": ok_count,
        "rejected_transactions": err_count,
        "audit_log": log
    }}
'''

    # 20..24: Category D: Obfuscated copies
    if 20 <= idx <= 24:
        d_idx = idx - 20
        return f'''# Financial Transaction Validator - Modified Copy {d_idx + 1}
# Registration: {reg}

def validate_transaction(tx):
    _ = {d_idx} * 100
    if not isinstance(tx, dict):
        return False, "Invalid record format"
    if "tx_id" not in tx or "amount" not in tx or "type" not in tx:
        return False, "Missing mandatory fields"
    if not isinstance(tx["amount"], (int, float)) or tx["amount"] <= 0:
        return False, "Amount must be positive number"
    if tx["type"] not in ("credit", "debit"):
        return False, "Transaction type must be 'credit' or 'debit'"
    return True, "Valid"

def process_ledger(initial_balance, transactions):
    current_balance = float(initial_balance) + 0.0
    valid_count = 0
    rejected_count = 0
    audit_log = []
    
    for tx in transactions:
        is_valid, msg = validate_transaction(tx)
        if not is_valid:
            rejected_count += 1
            audit_log.append({{"tx_id": tx.get("tx_id", "UNKNOWN"), "status": "REJECTED", "reason": msg}})
            continue
            
        amt = float(tx["amount"])
        if tx["type"] == "debit":
            if current_balance < amt:
                rejected_count += 1
                audit_log.append({{"tx_id": tx["tx_id"], "status": "REJECTED", "reason": "Insufficient funds"}})
                continue
            current_balance -= amt
        else:
            current_balance += amt
            
        valid_count += 1
        audit_log.append({{"tx_id": tx["tx_id"], "status": "ACCEPTED", "balance_after": round(current_balance, 2)}})
        
    return {{
        "initial_balance": initial_balance,
        "final_balance": round(current_balance, 2),
        "valid_transactions": valid_count,
        "rejected_transactions": rejected_count,
        "audit_log": audit_log
    }}
'''

    # 25..29: Category E: Alternative algorithms
    e_idx = idx - 25
    alt = [
        # E0: Rolling window fraud detection
        f'''"""Rolling Balance Fraud Heuristic
Registration: {reg}
"""
def rolling_window_ledger(init_bal, txs, max_single_debit=5000):
    b = init_bal
    v, r = 0, 0
    for t in txs:
        if isinstance(t, dict) and t.get("amount", 0) > 0:
            if t.get("type") == "debit" and t["amount"] > max_single_debit:
                r += 1  # Flagged by fraud threshold
            elif t.get("type") == "debit" and b >= t["amount"]:
                b -= t["amount"]
                v += 1
            elif t.get("type") == "credit":
                b += t["amount"]
                v += 1
            else:
                r += 1
        else:
            r += 1
    return {{"initial_balance": init_bal, "final_balance": round(b, 2), "valid": v, "rejected": r}}
''',
        # E1: Event sourcing snapshot model
        f'''"""Event Sourced Financial State
Registration: {reg}
"""
def replay_events(seed, events):
    snapshots = [seed]
    acc_events = []
    rej_events = []
    for e in events:
        curr = snapshots[-1]
        amt = e.get("amount", 0)
        if e.get("type") == "credit" and amt > 0:
            snapshots.append(curr + amt)
            acc_events.append(e)
        elif e.get("type") == "debit" and 0 < amt <= curr:
            snapshots.append(curr - amt)
            acc_events.append(e)
        else:
            rej_events.append(e)
    return {{"initial_balance": seed, "final_balance": round(snapshots[-1], 2), "valid": len(acc_events), "rejected": len(rej_events)}}
''',
        # E2: Multi currency converter
        f'''"""Multi-Currency FX Ledger
Registration: {reg}
"""
FX_RATES = {{"USD": 1.0, "EUR": 1.1, "GBP": 1.3}}

def fx_process_ledger(usd_initial, txs):
    bal = usd_initial
    v, r = 0, 0
    for t in txs:
        curr = t.get("currency", "USD")
        rate = FX_RATES.get(curr, 1.0)
        usd_amt = t.get("amount", 0) * rate
        if usd_amt > 0:
            if t.get("type") == "credit":
                bal += usd_amt; v += 1
            elif t.get("type") == "debit" and bal >= usd_amt:
                bal -= usd_amt; v += 1
            else:
                r += 1
        else:
            r += 1
    return {{"initial_balance": usd_initial, "final_balance": round(bal, 2), "valid": v, "rejected": r}}
''',
        # E3: Cash reserve requirement model
        f'''"""Reserve Ratio Enforcing Ledger
Registration: {reg}
"""
RESERVE_RATIO = 0.10

def reserve_ledger(start, txs):
    bal = start
    v, r = 0, 0
    for t in txs:
        amt = t.get("amount", 0)
        reserve = bal * RESERVE_RATIO
        if t.get("type") == "credit" and amt > 0:
            bal += amt; v += 1
        elif t.get("type") == "debit" and amt > 0 and (bal - amt) >= reserve:
            bal -= amt; v += 1
        else:
            r += 1
    return {{"initial_balance": start, "final_balance": round(bal, 2), "valid": v, "rejected": r}}
''',
        # E4: Pandas DataFrame simulation
        f'''"""Vectorized Simulation Ledger
Registration: {reg}
"""
def tabular_ledger(initial, records):
    valid_txs = [r for r in records if isinstance(r, dict) and r.get("amount", 0) > 0 and r.get("type") in ("credit", "debit")]
    bal = initial
    v, r = 0, len(records) - len(valid_txs)
    for t in valid_txs:
        if t["type"] == "credit":
            bal += t["amount"]; v += 1
        elif bal >= t["amount"]:
            bal -= t["amount"]; v += 1
        else:
            r += 1
    return {{"initial_balance": initial, "final_balance": round(bal, 2), "valid": v, "rejected": r}}
'''
    ]
    return alt[e_idx]


# ==============================================================================
# ASSIGNMENT 5: CA-05: Text Processing Toolkit
# ==============================================================================
_CA05_BASE = '''# Text Processing Toolkit
# Reference Implementation

import string

def count_word_frequencies(text):
    """Calculates frequency of each normalized word in text."""
    if not text:
        return {}
    clean = text.lower()
    for punct in string.punctuation:
        clean = clean.replace(punct, " ")
    words = clean.split()
    freq = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return freq

def is_palindrome(text):
    """Checks whether the alphanumeric sequence is a palindrome."""
    if not text:
        return True
    filtered = "".join(ch.lower() for ch in text if ch.isalnum())
    return filtered == filtered[::-1]

def analyze_text_statistics(text):
    """Computes total characters, words, sentences, and vocabulary size."""
    if not text:
        return {"char_count": 0, "word_count": 0, "sentence_count": 0, "unique_words": 0}
    freq = count_word_frequencies(text)
    words = sum(freq.values())
    sentences = sum(text.count(end) for end in (".", "!", "?"))
    return {
        "char_count": len(text),
        "word_count": words,
        "sentence_count": max(sentences, 1) if words > 0 else 0,
        "unique_words": len(freq)
    }

if __name__ == "__main__":
    sample = "A man, a plan, a canal: Panama! Was it a car or a cat I saw?"
    print("Freq:", count_word_frequencies(sample))
    print("Is Palindrome:", is_palindrome(sample))
    print("Stats:", analyze_text_statistics(sample))
'''

def _get_ca05_code(idx: int, reg: str) -> str:
    indep = [
        # 0: OOP TextAnalyzer
        f'''"""OOP Text Processing Toolkit
Registration: {reg}
"""
import re
from collections import Counter

class TextAnalyzer:
    def __init__(self, raw_text: str):
        self.text = raw_text or ""
        self.words = re.findall(r'\\b\\w+\\b', self.text.lower())

    def word_frequencies(self) -> dict:
        return dict(Counter(self.words))

    def check_palindrome(self) -> bool:
        clean = "".join(re.findall(r'[a-zA-Z0-9]', self.text.lower()))
        return clean == clean[::-1]

    def summary(self) -> dict:
        sentences = len(re.split(r'[.!?]+', self.text.strip())) if self.text.strip() else 0
        return {{
            "char_count": len(self.text),
            "word_count": len(self.words),
            "sentence_count": sentences,
            "unique_words": len(set(self.words))
        }}
''',
        # 1: Functional pipeline
        f'''"""Functional Text Processing
Registration: {reg}
"""
def sanitize_chars(s):
    return "".join(filter(str.isalnum, s.lower()))

def functional_palindrome(s):
    c = sanitize_chars(s)
    return c == c[::-1]

def extract_tokens(s):
    return "".join(c if c.isalnum() else " " for c in s.lower()).split()

def compute_freqs(s):
    tokens = extract_tokens(s)
    d = {{}}
    for t in tokens:
        d[t] = d.get(t, 0) + 1
    return d

def text_stats(s):
    f = compute_freqs(s)
    return {{
        "char_count": len(s),
        "word_count": sum(f.values()),
        "sentence_count": max(1, s.count(".") + s.count("!") + s.count("?")) if s else 0,
        "unique_words": len(f)
    }}
''',
        # 2: Two-pointer palindrome & dictionary tokenizer
        f'''"""Two-Pointer Palindrome and Word Frequencies
Registration: {reg}
"""
def two_pointer_palindrome(text):
    if not text: return True
    l, r = 0, len(text) - 1
    while l < r:
        while l < r and not text[l].isalnum(): l += 1
        while l < r and not text[r].isalnum(): r -= 1
        if text[l].lower() != text[r].lower(): return False
        l += 1; r -= 1
    return True

def manual_word_count(text):
    words = []
    curr = []
    for ch in text.lower():
        if ch.isalnum(): curr.append(ch)
        elif curr:
            words.append("".join(curr))
            curr = []
    if curr: words.append("".join(curr))
    counts = {{}}
    for w in words: counts[w] = counts.get(w, 0) + 1
    return counts
''',
        # 3: Lexical diversity and text toolkit
        f'''"""Lexical Diversity and String Toolkit
Registration: {reg}
"""
def get_words(t):
    clean = "".join(c if c.isalnum() else " " for c in t.lower())
    return clean.split()

def lexical_diversity(t):
    words = get_words(t)
    if not words: return 0.0
    return round(len(set(words)) / len(words), 3)

def check_symmetric_text(t):
    s = "".join(c.lower() for c in t if c.isalnum())
    return s == s[::-1]

def full_analysis(t):
    w = get_words(t)
    return {{
        "char_count": len(t),
        "word_count": len(w),
        "sentence_count": t.count(".") + t.count("!") + t.count("?"),
        "unique_words": len(set(w)),
        "diversity": lexical_diversity(t)
    }}
''',
        # 4: Dataclass based toolkit
        f'''"""Dataclass Text Processor
Registration: {reg}
"""
from dataclasses import dataclass
import string

@dataclass
class TextMetrics:
    raw: str
    
    def words(self):
        c = self.raw.lower()
        for p in string.punctuation: c = c.replace(p, " ")
        return c.split()
        
    def is_pal(self):
        filtered = [ch.lower() for ch in self.raw if ch.isalnum()]
        return filtered == filtered[::-1]
        
    def metrics(self):
        w = self.words()
        return {{
            "char_count": len(self.raw),
            "word_count": len(w),
            "sentence_count": sum(self.raw.count(x) for x in ".!?"),
            "unique_words": len(set(w))
        }}
''',
        # 5: While loop character scanner
        f'''"""Iterative Character Scanner
Registration: {reg}
"""
def while_count_words(content):
    counts = {{}}
    i = 0
    buf = []
    while i < len(content):
        c = content[i].lower()
        if c.isalnum(): buf.append(c)
        else:
            if buf:
                term = "".join(buf)
                counts[term] = counts.get(term, 0) + 1
                buf = []
        i += 1
    if buf:
        term = "".join(buf)
        counts[term] = counts.get(term, 0) + 1
    return counts

def while_palindrome(content):
    filt = [ch.lower() for ch in content if ch.isalnum()]
    i, j = 0, len(filt) - 1
    while i < j:
        if filt[i] != filt[j]: return False
        i += 1; j -= 1
    return True
''',
        # 6: Regex based toolkit
        f'''"""Regular Expression Text Analysis
Registration: {reg}
"""
import re

def regex_frequencies(text):
    tokens = re.findall(r'[a-zA-Z0-9]+', text.lower())
    d = {{}}
    for t in tokens: d[t] = d.get(t, 0) + 1
    return d

def regex_palindrome(text):
    letters = "".join(re.findall(r'[a-zA-Z0-9]', text.lower()))
    return letters == letters[::-1]

def regex_stats(text):
    w = re.findall(r'[a-zA-Z0-9]+', text.lower())
    s = re.split(r'[.!?]+', text)
    return {{
        "char_count": len(text),
        "word_count": len(w),
        "sentence_count": len([x for x in s if x.strip()]),
        "unique_words": len(set(w))
    }}
''',
        # 7: Recursive palindrome & accumulator
        f'''"""Recursive String Analysis
Registration: {reg}
"""
def rec_is_pal(s):
    if len(s) <= 1: return True
    if s[0] != s[-1]: return False
    return rec_is_pal(s[1:-1])

def palindrome_wrapper(text):
    cleaned = "".join(c.lower() for c in text if c.isalnum())
    return rec_is_pal(cleaned)

def parse_frequencies(text):
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    res = {{}}
    for w in words: res[w] = res.get(w, 0) + 1
    return res
''',
        # 8: Readability score approximation
        f'''"""Text Readability & Statistics
Registration: {reg}
"""
def extract_clean_words(t):
    return "".join(ch if ch.isalnum() else " " for ch in t.lower()).split()

def analyze_readability(t):
    words = extract_clean_words(t)
    sentences = max(1, t.count(".") + t.count("!") + t.count("?"))
    chars = len(t)
    avg_word_len = round(sum(len(w) for w in words) / len(words), 2) if words else 0.0
    return {{
        "char_count": chars,
        "word_count": len(words),
        "sentence_count": sentences,
        "unique_words": len(set(words)),
        "avg_word_len": avg_word_len
    }}
''',
        # 9: Top-K words and N-grams
        f'''"""N-Gram and Top-K Word Analyzer
Registration: {reg}
"""
def get_ngrams(text, n=2):
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

def top_k_frequencies(text, k=5):
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    counts = {{}}
    for w in words: counts[w] = counts.get(w, 0) + 1
    return sorted(counts.items(), key=lambda x: x[1], reverse=True)[:k]
'''
    ]

    if idx < 10:
        return indep[idx]

    # 10..14: Category B: Changed identifiers
    if 10 <= idx <= 14:
        v_idx = idx - 10
        tuples = [
            ("word_freq", "check_pal", "text_stats", "input_string", "clean_text"),
            ("token_distribution", "test_palindrome", "compute_stats", "source_doc", "stripped_body"),
            ("get_word_counts", "is_symmetric_str", "measure_text", "raw_content", "filtered_content"),
            ("calculate_frequencies", "verify_palindrome", "text_metric_collector", "sentence_block", "processed_data"),
            ("frequency_scanner", "palindrome_evaluator", "summarize_text_features", "passage", "normalized_passage")
        ]
        fn1, fn2, fn3, var_in, var_clean = tuples[v_idx]
        return f'''# Text Processing Toolkit - Identifier Variant {v_idx + 1}
# Registration: {reg}

import string

def {fn1}({var_in}):
    if not {var_in}:
        return {{}}
    {var_clean} = {var_in}.lower()
    for symbol in string.punctuation:
        {var_clean} = {var_clean}.replace(symbol, " ")
    token_list = {var_clean}.split()
    freq_map = {{}}
    for token in token_list:
        freq_map[token] = freq_map.get(token, 0) + 1
    return freq_map

def {fn2}({var_in}):
    if not {var_in}:
        return True
    pure_chars = "".join(c.lower() for c in {var_in} if c.isalnum())
    return pure_chars == pure_chars[::-1]

def {fn3}({var_in}):
    if not {var_in}:
        return {{"char_count": 0, "word_count": 0, "sentence_count": 0, "unique_words": 0}}
    distribution = {fn1}({var_in})
    total_tokens = sum(distribution.values())
    sentence_stops = sum({var_in}.count(end) for end in (".", "!", "?"))
    return {{
        "char_count": len({var_in}),
        "word_count": total_tokens,
        "sentence_count": max(sentence_stops, 1) if total_tokens > 0 else 0,
        "unique_words": len(distribution)
    }}
'''

    # 15..19: Category C: Altered syntax
    if 15 <= idx <= 19:
        c_idx = idx - 15
        return f'''# Text Processing Toolkit - Syntax Variant {c_idx + 1}
# Registration: {reg}

def count_word_frequencies(text):
    if not text:
        return {{}}
    cleaned = "".join(c.lower() if c.isalnum() else " " for c in text)
    words = cleaned.split()
    counts = {{}}
    i = 0
    while i < len(words):
        w = words[i]
        counts[w] = counts.get(w, 0) + 1
        i += 1
    return counts

def is_palindrome(text):
    chars = [c.lower() for c in text if c.isalnum()]
    return all(chars[i] == chars[len(chars) - 1 - i] for i in range(len(chars) // 2))

def analyze_text_statistics(text):
    if not text:
        return {{"char_count": 0, "word_count": 0, "sentence_count": 0, "unique_words": 0}}
    freq = count_word_frequencies(text)
    w_count = sum(freq.values())
    s_count = sum(text.count(p) for p in [".", "!", "?"])
    return {{
        "char_count": len(text),
        "word_count": w_count,
        "sentence_count": s_count if s_count > 0 else (1 if w_count > 0 else 0),
        "unique_words": len(freq)
    }}
'''

    # 20..24: Category D: Obfuscated copies
    if 20 <= idx <= 24:
        d_idx = idx - 20
        return f'''# Text Processing Toolkit - Modified Copy {d_idx + 1}
# Registration: {reg}

import string

def count_word_frequencies(text):
    _temp = {d_idx} + 1
    if not text or len(text) == 0:
        return {{}}
    clean = text.lower()
    for punct in string.punctuation:
        clean = clean.replace(punct, " ")
    words = clean.split()
    freq = {{}}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    return freq

def is_palindrome(text):
    if not text:
        return True
    filtered = "".join(ch.lower() for ch in text if ch.isalnum())
    reversed_str = filtered[::-1]
    return bool(filtered == reversed_str)

def analyze_text_statistics(text):
    if not text:
        return {{"char_count": 0, "word_count": 0, "sentence_count": 0, "unique_words": 0}}
    freq = count_word_frequencies(text)
    words = sum(freq.values())
    sentences = sum(text.count(end) for end in (".", "!", "?"))
    return {{
        "char_count": len(text),
        "word_count": words,
        "sentence_count": max(sentences, 1) if words > 0 else 0,
        "unique_words": len(freq)
    }}
'''

    # 25..29: Category E: Alternative algorithms
    e_idx = idx - 25
    alt = [
        # E0: collections.Counter
        f'''"""Counter Based Text Toolkit
Registration: {reg}
"""
from collections import Counter
import re

def counter_frequency(t):
    return dict(Counter(re.findall(r'\\w+', t.lower())))

def deque_palindrome(t):
    from collections import deque
    d = deque(c.lower() for c in t if c.isalnum())
    while len(d) > 1:
        if d.popleft() != d.pop(): return False
    return True
''',
        # E1: Character Vowel / Consonant ratio
        f'''"""Phonetic Vowel Consonant Ratio
Registration: {reg}
"""
def analyze_letters(t):
    vowels = set("aeiou")
    v_cnt, c_cnt = 0, 0
    for ch in t.lower():
        if ch.isalpha():
            if ch in vowels: v_cnt += 1
            else: c_cnt += 1
    return {{"vowels": v_cnt, "consonants": c_cnt, "ratio": round(v_cnt / c_cnt, 2) if c_cnt > 0 else 0.0}}
''',
        # E2: Markov text bigram model
        f'''"""Markov Bigram Frequency
Registration: {reg}
"""
def markov_bigrams(text):
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    transitions = {{}}
    for i in range(len(words) - 1):
        w1, w2 = words[i], words[i+1]
        transitions.setdefault(w1, []).append(w2)
    return transitions
''',
        # E3: Levenshtein distance comparator
        f'''"""Levenshtein Distance Metric
Registration: {reg}
"""
def edit_distance(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0]*(n+1) for _ in range(m+1)]
    for i in range(m+1): dp[i][0] = i
    for j in range(n+1): dp[0][j] = j
    for i in range(1, m+1):
        for j in range(1, n+1):
            cost = 0 if s1[i-1] == s2[j-1] else 1
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
    return dp[m][n]
''',
        # E4: Case-folding Trie
        f'''"""Prefix Trie Frequency Counter
Registration: {reg}
"""
class TrieNode:
    def __init__(self):
        self.children = {{}}
        self.count = 0

def build_trie(text):
    root = TrieNode()
    words = "".join(c if c.isalnum() else " " for c in text.lower()).split()
    for w in words:
        curr = root
        for ch in w:
            curr = curr.children.setdefault(ch, TrieNode())
        curr.count += 1
    return root
'''
    ]
    return alt[e_idx]
