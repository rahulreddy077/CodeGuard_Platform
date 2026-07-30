import unittest
import os
import ast
from modules.ast.parser import parse_code, ast_to_dict, ParserError
from modules.ast.normalizer import normalize_code, normalize_ast
from modules.ast.fingerprint import generate_fingerprint, hash_fingerprint
from modules.ast.utils import count_nodes, get_functions, get_classes

class TestASTParserModule(unittest.TestCase):
    def setUp(self):
        # Determine path to samples
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.samples_dir = os.path.join(base_dir, "tests", "samples")
        
        # Load sample files
        with open(os.path.join(self.samples_dir, "original.py"), "r", encoding="utf-8") as f:
            self.original_code = f.read()
            
        with open(os.path.join(self.samples_dir, "renamed.py"), "r", encoding="utf-8") as f:
            self.renamed_code = f.read()
            
        with open(os.path.join(self.samples_dir, "loop_changed.py"), "r", encoding="utf-8") as f:
            self.loop_changed_code = f.read()
            
        with open(os.path.join(self.samples_dir, "comments_removed.py"), "r", encoding="utf-8") as f:
            self.comments_removed_code = f.read()
            
        with open(os.path.join(self.samples_dir, "reformatted.py"), "r", encoding="utf-8") as f:
            self.reformatted_code = f.read()

    def test_parser_success(self):
        # Assert parser works on all five files
        for code, name in [
            (self.original_code, "original"),
            (self.renamed_code, "renamed"),
            (self.loop_changed_code, "loop_changed"),
            (self.comments_removed_code, "comments_removed"),
            (self.reformatted_code, "reformatted")
        ]:
            try:
                tree = parse_code(code, language="python")
                self.assertIsNotNone(tree, f"Parser returned None for {name}")
                
                # Check dict serialization
                d = ast_to_dict(tree, language="python")
                self.assertIsInstance(d, dict, f"ast_to_dict should return a dict for {name}")
                self.assertEqual(d["_type"], "Module")
            except Exception as e:
                self.fail(f"Failed to parse {name}: {str(e)}")

    def test_parser_syntax_error(self):
        invalid_code = "def invalid_func(\n    return 42"
        with self.assertRaises(ParserError):
            parse_code(invalid_code, language="python")

    def test_normalizer(self):
        # Normalize original code
        orig_normalized = normalize_code(self.original_code, language="python")
        
        # Normalize comments_removed
        removed_normalized = normalize_code(self.comments_removed_code, language="python")
        
        # Normalize reformatted
        reformatted_normalized = normalize_code(self.reformatted_code, language="python")
        
        # They should match exactly (comments and spacing removed, AST-unparse canonical formatting)
        self.assertEqual(orig_normalized, removed_normalized)
        self.assertEqual(orig_normalized, reformatted_normalized)
        
        # Check that docstrings are actually removed
        self.assertNotIn("Computes the greatest common divisor", orig_normalized)
        self.assertNotIn("Keep looping until y becomes zero", orig_normalized)

    def test_fingerprint_variable_renaming(self):
        tree_orig = parse_code(self.original_code, language="python")
        tree_renamed = parse_code(self.renamed_code, language="python")
        
        fp_orig = generate_fingerprint(tree_orig, exclude_context=True, language="python")
        fp_renamed = generate_fingerprint(tree_renamed, exclude_context=True, language="python")
        
        # The fingerprint should match exactly despite variable and function renames
        self.assertEqual(fp_orig, fp_renamed)
        self.assertIn("FunctionDef", fp_orig)
        self.assertIn("While", fp_orig)

    def test_fingerprint_loop_changed(self):
        tree_orig = parse_code(self.original_code, language="python")
        tree_loop = parse_code(self.loop_changed_code, language="python")
        
        fp_orig = generate_fingerprint(tree_orig, exclude_context=True, language="python")
        fp_loop = generate_fingerprint(tree_loop, exclude_context=True, language="python")
        
        # The fingerprint should differ as one uses a while loop and the other a for loop
        self.assertNotEqual(fp_orig, fp_loop)
        self.assertIn("While", fp_orig)
        self.assertIn("For", fp_loop)

    def test_utilities(self):
        tree = parse_code(self.original_code, language="python")
        
        funcs = get_functions(tree, language="python")
        classes = get_classes(tree, language="python")
        nodes_count = count_nodes(tree, language="python")
        
        self.assertEqual(funcs, ["compute_gcd"])
        self.assertEqual(classes, [])
        self.assertGreater(nodes_count, 10)

    def test_variable_normalization(self):
        norm = normalize_code(self.original_code, language="python")
        # Variables x, y, temp in original.py should map to VAR_1, VAR_2, VAR_3
        self.assertIn("VAR_1", norm)
        self.assertIn("VAR_2", norm)
        self.assertIn("VAR_3", norm)
        self.assertNotIn("temp", norm)
        # Function name 'compute_gcd' should be preserved (not renamed)
        self.assertIn("def compute_gcd(VAR_1, VAR_2):", norm)

    def test_fingerprint_hashing(self):
        tree = parse_code(self.original_code, language="python")
        fp = generate_fingerprint(tree, exclude_context=True, language="python")
        f_hash = hash_fingerprint(fp)
        
        self.assertEqual(len(f_hash), 64) # SHA256 length is 64 hex characters
        self.assertEqual(f_hash, hash_fingerprint(fp)) # Deterministic

if __name__ == "__main__":
    unittest.main()
