# Cyclomatic Complexity in CodeGuard: Defense & Report Overview

Cyclomatic complexity is a quantitative software metric that measures the structural complexity of a program by counting the number of linearly independent execution paths through its source code. In CodeGuard, this is computed using the open-source **Radon** library, which analyzes the AST control-flow graph of each function and increments the score for every decision point—such as `if` statements, `for` or `while` loops, and logical operators. For example, a standard function containing 3 nested `if` statements has 4 possible execution paths, yielding a cyclomatic complexity score of 4.

CodeGuard reports cyclomatic complexity for two key purposes:

1. **Maintainability Signal**: It provides clear pedagogical feedback to students and faculty regarding code quality and readability. Functions with high complexity are harder to test, debug, and maintain.
2. **Soft Plagiarism Signal**: In an assignment where students solve identical problem specifications, submissions typically exhibit similar baseline complexity. An unusually high complexity score compared to classmates' simpler solutions can indicate code obfuscation, automated wrapper injection, or structural adaptation of external code, highlighting the submission for faculty review.
