import os
import json

path1 = os.path.join("data", "whodunit", "_01_datasets", "codechef", "final_dataset.json")
with open(path1, "r", encoding="utf-8") as f:
    d1 = json.load(f)

all_problems = {}
for k, v in d1.items():
    if isinstance(v, dict):
        for prob_name, prob_val in v.items():
            all_problems[prob_name] = prob_val

print(f"Total problems: {len(all_problems)}")

human_counts = []
ai_counts = []
sample_ai = None
sample_human = None

for prob_id, prob in all_problems.items():
    hs = prob.get("human_solutions", [])
    ais = prob.get("ai_solutions", [])
    human_counts.append(len(hs))
    ai_counts.append(len(ais))
    if sample_ai is None and len(ais) > 0:
        sample_ai = ais[0]
    if sample_human is None and len(hs) > 0:
        sample_human = hs[0]

print(f"Human solutions per problem: min={min(human_counts)}, max={max(human_counts)}, sum={sum(human_counts)}")
print(f"AI solutions per problem: min={min(ai_counts)}, max={max(ai_counts)}, sum={sum(ai_counts)}")

print("\nSample human solution type and content:")
print("Type:", type(sample_human))
if isinstance(sample_human, dict):
    print("Keys:", list(sample_human.keys()))
    print("Has 'code' field?", "code" in sample_human)
    if "code" in sample_human:
        print("Code snippet (first 100 chars):", repr(sample_human["code"][:100]))

print("\nSample AI solution type and content:")
print("Type:", type(sample_ai))
if isinstance(sample_ai, dict):
    print("Keys:", list(sample_ai.keys()))
    print("Has 'code' field?", "code" in sample_ai)
    if "code" in sample_ai:
        print("Code snippet (first 100 chars):", repr(sample_ai["code"][:100]))
elif isinstance(sample_ai, str):
    print("AI solution is directly string! First 100 chars:", repr(sample_ai[:100]))
