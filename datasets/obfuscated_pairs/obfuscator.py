"""
CodeGuard - Obfuscation Engine
================================
Takes a piece of human-written Python source code and produces multiple
"disguised plagiarism" variants that preserve logic/behavior but change
surface structure - simulating how a student might disguise copied code.

Techniques implemented:
  1. Variable renaming        (identifier substitution)
  2. Statement reordering     (independent top-level statements shuffled)
  3. Loop conversion          (for-range <-> while)
  4. Dead code insertion      (no-op statements inserted)
  5. Operand reordering       (commutative expressions: a+b -> b+a)

Each technique returns valid, runnable Python that is logically equivalent
to the original. This is Step 1 of the CodeGuard pipeline: building the
labeled plagiarism-pair dataset used to train/evaluate the similarity engine.
"""

import ast
import random
import string
import copy
import astor  # pip install astor --break-system-packages


# ---------------------------------------------------------------------------
# 1. VARIABLE RENAMING
# ---------------------------------------------------------------------------
class VariableRenamer(ast.NodeTransformer):
    """Renames local variable names (not builtins/keywords/function names)."""

    PROTECTED = set(dir(__builtins__)) | {
        "self", "cls", "range", "len", "print", "True", "False", "None"
    }

    def __init__(self):
        self.mapping = {}

    def _new_name(self, old_name):
        if old_name in self.mapping:
            return self.mapping[old_name]
        new_name = "v_" + "".join(random.choices(string.ascii_lowercase, k=5))
        self.mapping[old_name] = new_name
        return new_name

    def visit_Name(self, node):
        if node.id in self.PROTECTED:
            return node
        node.id = self._new_name(node.id)
        return node

    def visit_arg(self, node):
        if node.arg in self.PROTECTED:
            return node
        node.arg = self._new_name(node.arg)
        return node

    def visit_FunctionDef(self, node):
        # Keep the function name itself unchanged (so callers still work),
        # but rename its parameters and body variables.
        node.args = self.generic_visit(node.args)
        node.body = [self.visit(stmt) for stmt in node.body]
        return node


def obfuscate_rename_variables(tree):
    tree = copy.deepcopy(tree)
    renamer = VariableRenamer()
    return renamer.visit(tree)


# ---------------------------------------------------------------------------
# 2. STATEMENT REORDERING (independent top-level statements within a block)
# ---------------------------------------------------------------------------
def _is_reorderable_block(statements):
    """Very conservative check: only reorder simple Assign statements that
    don't reference each other (heuristic, not a full dependency analysis)."""
    names_defined = set()
    for stmt in statements:
        if not isinstance(stmt, ast.Assign):
            return False
        for target in stmt.targets:
            if isinstance(target, ast.Name):
                names_defined.add(target.id)
    # Check none of the RHS expressions reference a name defined by a sibling
    for stmt in statements:
        for node in ast.walk(stmt.value):
            if isinstance(node, ast.Name) and node.id in names_defined:
                return False
    return True


class StatementReorderer(ast.NodeTransformer):
    def generic_visit(self, node):
        node = super().generic_visit(node)
        for field in ("body", "orelse", "finalbody"):
            block = getattr(node, field, None)
            if isinstance(block, list) and len(block) > 1:
                # find longest reorderable run of consecutive Assign stmts
                i = 0
                while i < len(block):
                    j = i
                    while j < len(block) and isinstance(block[j], ast.Assign):
                        j += 1
                    if j - i > 1 and _is_reorderable_block(block[i:j]):
                        chunk = block[i:j]
                        random.shuffle(chunk)
                        block[i:j] = chunk
                    i = max(j, i + 1)
                setattr(node, field, block)
        return node


def obfuscate_reorder_statements(tree):
    tree = copy.deepcopy(tree)
    return StatementReorderer().visit(tree)


# ---------------------------------------------------------------------------
# 3. LOOP CONVERSION: for i in range(...) -> equivalent while loop
# ---------------------------------------------------------------------------
class ForToWhileConverter(ast.NodeTransformer):
    def visit_For(self, node):
        self.generic_visit(node)
        is_range_call = (
            isinstance(node.iter, ast.Call)
            and isinstance(node.iter.func, ast.Name)
            and node.iter.func.id == "range"
            and isinstance(node.target, ast.Name)
        )
        if not is_range_call:
            return node

        args = node.iter.args
        if len(args) == 1:
            start, stop, step = ast.Constant(value=0), args[0], ast.Constant(value=1)
        elif len(args) == 2:
            start, stop, step = args[0], args[1], ast.Constant(value=1)
        elif len(args) == 3:
            start, stop, step = args
        else:
            return node

        var = node.target.id
        init = ast.Assign(targets=[ast.Name(id=var, ctx=ast.Store())], value=start)
        cond = ast.Compare(left=ast.Name(id=var, ctx=ast.Load()),
                            ops=[ast.Lt()], comparators=[stop])
        increment = ast.AugAssign(
            target=ast.Name(id=var, ctx=ast.Store()), op=ast.Add(), value=step
        )
        while_node = ast.While(test=cond, body=node.body + [increment], orelse=node.orelse)
        return [init, while_node]


def obfuscate_for_to_while(tree):
    tree = copy.deepcopy(tree)
    return ForToWhileConverter().visit(tree)


# ---------------------------------------------------------------------------
# 4. DEAD CODE INSERTION
# ---------------------------------------------------------------------------
class DeadCodeInserter(ast.NodeTransformer):
    def _dead_stmt(self):
        junk_var = "_unused_" + "".join(random.choices(string.ascii_lowercase, k=4))
        return ast.Assign(
            targets=[ast.Name(id=junk_var, ctx=ast.Store())],
            value=ast.Constant(value=0),
        )

    def generic_visit(self, node):
        node = super().generic_visit(node)
        if isinstance(getattr(node, "body", None), list) and node.body:
            insert_at = random.randint(0, len(node.body))
            node.body.insert(insert_at, self._dead_stmt())
        return node


def obfuscate_insert_dead_code(tree):
    tree = copy.deepcopy(tree)
    return DeadCodeInserter().visit(tree)


# ---------------------------------------------------------------------------
# 5. OPERAND REORDERING for commutative operators (+, *)
# ---------------------------------------------------------------------------
class OperandReorderer(ast.NodeTransformer):
    COMMUTATIVE = (ast.Add, ast.Mult)

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, self.COMMUTATIVE) and random.random() < 0.7:
            node.left, node.right = node.right, node.left
        return node


def obfuscate_reorder_operands(tree):
    tree = copy.deepcopy(tree)
    return OperandReorderer().visit(tree)


# ---------------------------------------------------------------------------
# Driver: apply all techniques and return labeled pairs
# ---------------------------------------------------------------------------
TECHNIQUES = {
    "variable_renaming": obfuscate_rename_variables,
    "statement_reordering": obfuscate_reorder_statements,
    "loop_conversion": obfuscate_for_to_while,
    "dead_code_insertion": obfuscate_insert_dead_code,
    "operand_reordering": obfuscate_reorder_operands,
}


def generate_obfuscated_variants(source_code):
    """
    Given original Python source, returns a dict:
      { technique_name: obfuscated_source_code }
    for every technique that successfully parses and transforms the code.
    Techniques that fail (e.g. syntax not applicable) are skipped safely.
    """
    results = {}
    try:
        original_tree = ast.parse(source_code)
    except SyntaxError as e:
        raise ValueError(f"Input source code has a syntax error: {e}")

    for name, func in TECHNIQUES.items():
        try:
            new_tree = func(original_tree)
            ast.fix_missing_locations(new_tree)
            obfuscated_code = astor.to_source(new_tree)
            # Sanity check: obfuscated code must still be valid Python
            compile(obfuscated_code, "<obfuscated>", "exec")
            results[name] = obfuscated_code
        except Exception as e:
            print(f"  [skipped: {name}] {e}")
    return results


def generate_combined_obfuscation(source_code, techniques=None):
    """
    Applies multiple techniques in sequence (compounded obfuscation) -
    this is what you'll use for the 'obfuscated + AI-generated' novelty
    experiment: apply this to CodeLlama-generated code, not just human code.
    """
    if techniques is None:
        techniques = list(TECHNIQUES.keys())
    tree = ast.parse(source_code)
    for name in techniques:
        tree = TECHNIQUES[name](tree)
        ast.fix_missing_locations(tree)
    code = astor.to_source(tree)
    compile(code, "<combined_obfuscated>", "exec")
    return code


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    sample_code = '''
def is_prime(n):
    if n < 2:
        return False
    a = 2
    b = n
    for i in range(2, n):
        if n % i == 0:
            return False
    return True
'''

    print("=" * 70)
    print("ORIGINAL CODE:")
    print("=" * 70)
    print(sample_code)

    variants = generate_obfuscated_variants(sample_code)

    for technique, code in variants.items():
        print("=" * 70)
        print(f"TECHNIQUE: {technique}")
        print("=" * 70)
        print(code)

    print("=" * 70)
    print("COMBINED (ALL TECHNIQUES APPLIED IN SEQUENCE):")
    print("=" * 70)
    try:
        combined = generate_combined_obfuscation(sample_code)
        print(combined)
    except Exception as e:
        print(f"Combined obfuscation failed: {e}")
