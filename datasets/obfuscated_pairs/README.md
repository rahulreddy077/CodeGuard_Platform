# CodeGuard — Step 1: Plagiarism Dataset Generator

This is a **working, tested** piece of CodeGuard: an obfuscation engine that
takes real Python code and generates disguised-plagiarism variants, plus a
dataset builder that turns those into labeled training/test pairs.

## What's in here

- `obfuscator.py` — 5 obfuscation techniques (variable renaming, statement
  reordering, loop conversion, dead code insertion, operand reordering),
  each implemented with Python's `ast` module. Also includes
  `generate_combined_obfuscation()` which stacks all 5 techniques — this is
  what you'll use for the "compounded obfuscation" novelty experiment.
- `build_dataset.py` — reads a folder of `.py` solution files and produces
  a labeled CSV (`original_code, variant_code, technique, label`).
- `solutions/` — 3 example solutions (is_prime, factorial, fibonacci) to
  test with.
- `sample_pairs.csv` — the actual output from running this on the 3 examples
  (24 labeled pairs) — open it to see exactly what the data looks like.

## How to run it yourself

```bash
pip install astor
python build_dataset.py --input_dir ./solutions --output pairs.csv
```

## How to grow this into your real dataset

1. **Add more human-written solutions.** Drop more `.py` files into
   `solutions/` — one function/problem per file. Good free sources:
   Project CodeNet (Kaggle), your own classmates' past assignment
   solutions (with permission), or your own solutions to common
   CS-1/CS-2 problems (sorting, searching, recursion, etc.). Aim for
   50-100 distinct problems to get a meaningfully sized dataset.

2. **Generate AI-written code with Ollama (do this on your own laptop —
   this environment has no internet access to download models):**
   ```bash
   ollama pull codellama
   ollama run codellama "Write a Python function to check if a number is prime"
   ```
   Save each output as a `.py` file in a separate `ai_generated/` folder,
   labeled `ai_generated=1`. Do the same later with ChatGPT-written code
   (label the *source* generator too — you'll need this for the
   cross-generator experiment) in an `ai_generated_chatgpt/` folder.

3. **Build the "compounded obfuscation + AI-generated" experiment set**
   (your strongest novelty point): run
   `generate_combined_obfuscation()` on your AI-generated files too, not
   just human ones. Compare detection accuracy on:
   - human code (baseline)
   - obfuscated human code
   - AI-generated code
   - obfuscated AI-generated code ← the untested combination

4. **Next module to build:** once you have ~100+ labeled pairs, the next
   step is feeding `original_code`/`variant_code` pairs into GraphCodeBERT
   to get embeddings and compute cosine similarity — that's Step 2
   (plagiarism engine). I can build that next whenever you're ready;
   it needs a GPU, so Google Colab is the easiest place to run it.

## A note on limits (be upfront about these to your panel)

- `statement_reordering` only reorders simple, independent `Assign`
  statements — it doesn't do full data-flow dependency analysis, so it's
  conservative on purpose (safer than reordering something that breaks
  the code).
- `dead_code_insertion` inserts genuinely unused variable assignments —
  it doesn't insert dead branches or unreachable code yet, which would
  be a reasonable extension if you want a 6th technique.
- All techniques operate on Python only right now — extending to
  Java/C++ would need a different AST library (e.g., tree-sitter, which
  is already in your tech stack for the structural-similarity module).
