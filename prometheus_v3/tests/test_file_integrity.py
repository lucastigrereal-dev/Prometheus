Testes para File Integrity System
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from file_integrity.file_hash import FileHasher
from file_integrity.file_index import FileIndex, FileRecord
from file_integrity.file_integrity_service import FileIntegrityService


class TestFileHasher(unittest.TestCase):
    """Testes para FileHasher"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.hasher = FileHasher()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_hash_file(self):
        """Testa geração de hash de arquivo"""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Hello, Prometheus!")

        hash_val = self.hasher.hash_file(test_file)

        self.assertIsNotNone(hash_val)
        self.assertEqual(len(hash_val), 64)  # SHA-256 = 64 hex chars

    def test_hash_content(self):
        """Testa geração de hash de conteúdo"""
        content = "Hello, Prometheus!"

        hash_val = self.hasher.hash_content(content)

        self.assertIsNotNone(hash_val)
        self.assertEqual(len(hash_val), 64)

    def test_verify_file(self):
        """Testa verificação de arquivo"""
        test_file = self.test_dir / "test.txt"
        test_file.write_text("Hello, Prometheus!")

        # Gerar hash original
        original_hash = self.hasher.hash_file(test_file)

        # Verificar com hash correto
        self.assertTrue(self.hasher.verify_file(test_file, original_hash))

        # Modificar arquivo
        test_file.write_text("Modified content")

        # Verificar com hash antigo (deve falhar)
        self.assertFalse(self.hasher.verify_file(test_file, original_hash))

    def test_batch_hash(self):
        """Testa hash em batch"""
        files = []
        for i in range(3):
            test_file = self.test_dir / f"test{i}.txt"
            test_file.write_text(f"Content {i}")
            files.append(test_file)

        results = self.hasher.batch_hash(files)

        self.assertEqual(len(results), 3)
        self.assertTrue(all(v is not None for v in results.values()))


class TestFileIndex(unittest.TestCase):
    """Testes para FileIndex"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.index_path = self.test_dir / "test_index.json"
        self.index = FileIndex(self.index_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_add_file(self):
        """Testa adição de arquivo"""
        record = FileRecord(
            path="/test/file.py",
            hash="abc123",
            size_bytes=1024,
            modified_at="2025-11-19T10:00:00",
            indexed_at="2025-11-19T10:00:00",
            status="valid",
            category="code"
        )

        success = self.index.add_file(record)

        self.assertTrue(success)
        self.assertIn("/test/file.py", self.index.records)

    def test_get_file(self):
        """Testa busca de arquivo"""
        record = FileRecord(
            path="/test/file.py",
            hash="abc123",
            size_bytes=1024,
            modified_at="2025-11-19T10:00:00",
            indexed_at="2025-11-19T10:00:00",
            status="valid",
            category="code"
        )

        self.index.add_file(record)

        found = self.index.get_file("/test/file.py")

        self.assertIsNotNone(found)
        self.assertEqual(found.hash, "abc123")

    def test_save_and_load(self):
        """Testa salvar e carregar índice"""
        record = FileRecord(
            path="/test/file.py",
            hash="abc123",
            size_bytes=1024,
            modified_at="2025-11-19T10:00:00",
            indexed_at="2025-11-19T10:00:00",
            status="valid",
            category="code"
        )

        self.index.add_file(record)
        self.index.save()

        # Criar novo índice e carregar
        new_index = FileIndex(self.index_path)

        self.assertEqual(len(new_index.records), 1)
        self.assertIn("/test/file.py", new_index.records)

    def test_list_files_with_filters(self):
        """Testa listagem com filtros"""
        # Adicionar múltiplos arquivos
        records = [
            FileRecord(
                path=f"/test/file{i}.py",
                hash=f"hash{i}",
                size_bytes=1024,
                modified_at="2025-11-19T10:00:00",
                indexed_at="2025-11-19T10:00:00",
                status="valid" if i % 2 == 0 else "modified",
                category="code",
                protected=(i == 0)
            )
            for i in range(5)
        ]

        for record in records:
            self.index.add_file(record)

        # Filtrar por status
        valid_files = self.index.list_files(status="valid")
        self.assertEqual(len(valid_files), 3)

        # Filtrar por protected
        protected_files = self.index.list_files(protected=True)
        self.assertEqual(len(protected_files), 1)


class TestFileIntegrityService(unittest.TestCase):
    """Testes para FileIntegrityService"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.index_path = self.test_dir / "test_index.json"
        self.service = FileIntegrityService(
            index_path=self.index_path,
            auto_save=True
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_register_file(self):
        """Testa registro de arquivo"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("print('Hello')")

        success = self.service.register_file(
            file_path=test_file,
            category="code",
            protected=True
        )

        self.assertTrue(success)

        record = self.service.index.get_file(str(test_file))
        self.assertIsNotNone(record)
        self.assertEqual(record.category, "code")
        self.assertTrue(record.protected)

    def test_verify_file_valid(self):
        """Testa verificação de arquivo válido"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("print('Hello')")

        self.service.register_file(test_file, category="code")

        result = self.service.verify_file(test_file)

        self.assertEqual(result["status"], "valid")

    def test_verify_file_modified(self):
        """Testa detecção de arquivo modificado"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("print('Hello')")

        self.service.register_file(test_file, category="code")

        # Modificar arquivo
        test_file.write_text("print('Modified')")

        result = self.service.verify_file(test_file)

        self.assertEqual(result["status"], "modified")
        self.assertIn("original_hash", result)
        self.assertIn("current_hash", result)

    def test_approve_modification(self):
        """Testa aprovação de modificação"""
        test_file = self.test_dir / "test.py"
        test_file.write_text("print('Hello')")

        self.service.register_file(test_file)

        # Modificar
        test_file.write_text("print('Modified')")

        # Aprovar
        success = self.service.approve_modification(str(test_file))

        self.assertTrue(success)

        # Verificar novamente (deve estar valid)
        result = self.service.verify_file(test_file)
        self.assertEqual(result["status"], "valid")


if __name__ == '__main__':
    unittest.main()
