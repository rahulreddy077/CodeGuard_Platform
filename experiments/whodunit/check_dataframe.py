import os
import json
import ast
import pandas as pd

json_path = os.path.join("data", "whodunit", "_01_datasets", "codechef", "final_dataset.json")
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []
for diff_level, problems in data.items():
    if not isinstance(problems, dict):
        continue
    for problem_id, prob in problems.items():
        # Human solutions
        for h_sol in prob.get("human_solutions", []):
            code_str = h_sol.get("code", "") if isinstance(h_sol, dict) else str(h_sol)
            rows.append({
                "code": code_str,
                "label": 0,
                "problem_id": problem_id,
                "source": "human"
            })
        # AI solutions
        for a_sol in prob.get("ai_solutions", []):
            code_str = a_sol if isinstance(a_sol, str) else a_sol.get("code", "")
            rows.append({
                "code": code_str,
                "label": 1,
                "problem_id": problem_id,
                "source": "gpt4"
            })

df = pd.DataFrame(rows)
print(f"Total rows built: {len(df)}")
print(f"Human count: {(df['source'] == 'human').sum()}")
print(f"GPT-4 count: {(df['source'] == 'gpt4').sum()}")
print(f"Unique problems: {df['problem_id'].nunique()}")

# Check ast.parse()
parse_failures = []
for idx, row in df.iterrows():
    try:
        ast.parse(row["code"])
    except Exception as e:
        parse_failures.append({
            "index": idx,
            "problem_id": row["problem_id"],
            "source": row["source"],
            "error": str(e)
        })

print(f"\nTotal ast.parse() failures: {len(parse_failures)}")
for pf in parse_failures[:10]:
    print(f"  - Problem: {pf['problem_id']}, Source: {pf['source']}, Error: {pf['error']}")
