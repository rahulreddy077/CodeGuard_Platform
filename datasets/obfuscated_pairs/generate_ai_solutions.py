import os
import glob
import json
import urllib.request
import urllib.error
import re

def get_signature(filepath):
    with open(filepath, 'r') as f:
        code = f.read()
    for line in code.split('\n'):
        if line.strip().startswith('def '):
            return line.strip()
    return None

def generate_solution(signature, filename):
    prompt = (
        f"You are a software engineer. Write a Python function with the signature:\n"
        f"{signature}\n"
        f"that implements the functionality described by the file name '{filename}' (e.g. gcd, bubble sort, etc.).\n"
        f"Return ONLY valid, executable Python code. Do NOT wrap the code in a markdown block, do not include any explanatory text, markdown comments, docstrings, or tests. Return just the function implementation."
    )
    
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "codellama:latest",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2
        }
    }
    
    headers = {"Content-Type": "application/json"}
    req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
    
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            code = res.get('response', '')
            return code
    except Exception as e:
        print(f"Error querying Ollama for {filename}: {e}")
        return None

def clean_code(response_text):
    # If the response contains markdown code fences, extract the contents
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    match = re.search(pattern, response_text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return response_text.strip()

def main():
    solutions_dir = "./solutions"
    output_dir = "./ai_generated"
    os.makedirs(output_dir, exist_ok=True)
    
    # List files and sort them to be deterministic
    files = sorted(glob.glob(os.path.join(solutions_dir, "*.py")))
    print(f"Found {len(files)} original solutions.")
    
    # We will generate AI solutions for 18 files (within the 15-20 range requested)
    target_count = 18
    selected_files = files[:target_count]
    
    success_count = 0
    for filepath in selected_files:
        filename = os.path.basename(filepath)
        print(f"Processing {filename}...")
        
        signature = get_signature(filepath)
        if not signature:
            print(f"  Could not find function signature for {filename}. Skipping.")
            continue
            
        print(f"  Signature: {signature}")
        response = generate_solution(signature, filename)
        if response:
            code = clean_code(response)
            # Ensure the output is not completely empty
            if code:
                out_path = os.path.join(output_dir, filename)
                with open(out_path, 'w') as f:
                    f.write(code)
                print(f"  Successfully wrote AI-generated solution to {out_path}")
                success_count += 1
            else:
                print(f"  Ollama returned empty response for {filename}")
        else:
            print(f"  Failed to generate solution for {filename}")
            
    print(f"\nDone. Successfully generated {success_count} AI solutions in {output_dir}")

if __name__ == "__main__":
    main()
