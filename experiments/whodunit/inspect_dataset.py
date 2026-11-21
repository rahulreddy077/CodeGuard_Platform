import os
import json

path1 = os.path.join("data", "whodunit", "_01_datasets", "codechef", "final_dataset.json")
path2 = os.path.join("data", "whodunit", "_01_datasets", "codechef", "final_successful_dataset.json")

print("Checking final_dataset.json:")
with open(path1, "r", encoding="utf-8") as f:
    d1 = json.load(f)

print("d1 type:", type(d1))
if isinstance(d1, dict):
    print("d1 top keys:", list(d1.keys()))
    # Let's inspect each top key
    all_problems = {}
    for k, v in d1.items():
        if isinstance(v, dict):
            for prob_name, prob_val in v.items():
                all_problems[prob_name] = prob_val
    print("Total problems aggregated across keys:", len(all_problems))
    if len(all_problems) > 0:
        sample_key = next(iter(all_problems))
        print("Sample problem key:", sample_key)
        print("Sample problem keys/type:", type(all_problems[sample_key]), 
              list(all_problems[sample_key].keys()) if isinstance(all_problems[sample_key], dict) else all_problems[sample_key])
        sample_val = all_problems[sample_key]
        if isinstance(sample_val, dict):
            if "human_solutions" in sample_val:
                print("human_solutions len:", len(sample_val["human_solutions"]))
                if sample_val["human_solutions"]:
                    print("human_solution[0] keys:", list(sample_val["human_solutions"][0].keys()) if isinstance(sample_val["human_solutions"][0], dict) else type(sample_val["human_solutions"][0]))
            if "ai_solutions" in sample_val:
                print("ai_solutions len:", len(sample_val["ai_solutions"]))
                if sample_val["ai_solutions"]:
                    print("ai_solution[0] keys:", list(sample_val["ai_solutions"][0].keys()) if isinstance(sample_val["ai_solutions"][0], dict) else type(sample_val["ai_solutions"][0]))

# Also check path2 if needed
if os.path.exists(path2):
    print("\nChecking final_successful_dataset.json:")
    with open(path2, "r", encoding="utf-8") as f:
        d2 = json.load(f)
    print("d2 type:", type(d2))
    if isinstance(d2, dict):
        print("d2 keys:", list(d2.keys())[:10], "... total:", len(d2))
