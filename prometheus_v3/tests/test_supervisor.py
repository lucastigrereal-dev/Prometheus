Testes para Supervisor
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from supervisor.change_diff_analyzer import ChangeDiffAnalyzer
from supervisor.code_boundary_protector import CodeBoundaryProtector


class TestChangeDiffAnalyzer(unittest.TestCase):
    """Testes para ChangeDiffAnalyzer"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.analyzer = ChangeDiffAnalyzer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_analyze_file_change(self):
        """Testa análise de mudança"""
        original = self.test_dir / "original.py"
        modified = self.test_dir / "modified.py"

        original.write_text("def hello():\n    print('Hello')\n")
        modified.write_text("def hello():\n    print('Hello, World!')\n")

        result = self.analyzer.analyze_file_change(original, modified)

        self.assertTrue(result.has_changes)
        self.assertGreater(result.total_changes, 0)

    def test_analyze_content_change(self):
        """Testa análise de conteúdo"""
        original = "line 1\nline 2\nline 3\n"
        modified = "line 1\nline 2 modified\nline 3\n"

        result = self.analyzer.analyze_content_change(original, modified)

        self.assertTrue(result.has_changes)
        self.assertEqual(result.lines_added, 1)
        self.assertEqual(result.lines_removed, 1)

    def test_no_changes(self):
        """Testa quando não há mudanças"""
        original = self.test_dir / "file.py"
        modified = self.test_dir / "file.py"

        original.write_text("unchanged content")

        result = self.analyzer.analyze_file_change(original, modified)

        self.assertFalse(result.has_changes)
        self.assertEqual(result.total_changes, 0)


class TestCodeBoundaryProtector(unittest.TestCase):
    """Testes para CodeBoundaryProtector"""

    def setUp(self):
        self.protector = CodeBoundaryProtector()

    def test_validate_valid_python(self):
        """Testa validação de código Python válido"""
        code = """
def hello():
    print('Hello, World!')

if __name__ == '__main__':
    hello()
"""

        violations = self.protector.validate_content(code, file_type="python")

        self.assertEqual(len(violations), 0)

    def test_detect_syntax_error(self):
        """Testa detecção de erro de sintaxe"""
        code = """
def hello()
    print('Missing colon')
"""

        violations = self.protector.validate_content(code, file_type="python")

        self.assertGreater(len(violations), 0)
        self.assertEqual(violations[0].violation_type, "syntax_error")

    def test_detect_forbidden_eval(self):
        """Testa detecção de eval()"""
        code = """
def unsafe():
    result = eval(user_input)
    return result
"""

        violations = self.protector.validate_content(code, file_type="python")

        # Deve detectar eval
        eval_violations = [v for v in violations if "eval" in v.description.lower()]
        self.assertGreater(len(eval_violations), 0)

    def test_detect_forbidden_exec(self):
        """Testa detecção de exec()"""
        code = """
def unsafe():
    exec(user_input)
"""

        violations = self.protector.validate_content(code, file_type="python")

        # Deve detectar exec
        exec_violations = [v for v in violations if "exec" in v.description.lower()]
        self.assertGreater(len(exec_violations), 0)

    def test_is_safe_to_modify(self):
        """Testa verificação de segurança"""
        temp_dir = Path(tempfile.mkdtemp())
        test_file = temp_dir / "test.py"

        # Código seguro
        test_file.write_text("def hello():\n    print('Hello')")

        is_safe, violations = self.protector.is_safe_to_modify(test_file)

        self.assertTrue(is_safe)
        self.assertEqual(len(violations), 0)

        # Código inseguro
        test_file.write_text("eval(input())")

        is_safe, violations = self.protector.is_safe_to_modify(test_file)

        self.assertFalse(is_safe)
        self.assertGreater(len(violations), 0)

        shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main()
