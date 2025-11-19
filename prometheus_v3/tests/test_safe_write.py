Testes para Safe-Write Engine
"""

import unittest
import tempfile
import shutil
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from safe_write.safe_write import SafeWriter, WriteOperation, WriteMode


class TestSafeWriter(unittest.TestCase):
    """Testes para SafeWriter"""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.test_dir / "backups"
        self.writer = SafeWriter(
            backup_dir=self.backup_dir,
            integrity_service=None,
            audit_logger=None,
            dry_run=False
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_write_new_file(self):
        """Testa criação de novo arquivo"""
        target = self.test_dir / "test.txt"
        content = "Hello, Prometheus!"

        result = self.writer.write_text(
            path=target,
            content=content,
            mode=WriteMode.CREATE
        )

        self.assertTrue(result.success)
        self.assertTrue(target.exists())
        self.assertEqual(target.read_text(), content)
        self.assertGreater(result.bytes_written, 0)

    def test_write_overwrite_with_backup(self):
        """Testa sobrescrita com backup"""
        target = self.test_dir / "test.txt"
        original = "Original"
        new_content = "New"

        # Criar original
        target.write_text(original)

        # Sobrescrever
        result = self.writer.write_text(
            path=target,
            content=new_content,
            mode=WriteMode.OVERWRITE,
            create_backup=True
        )

        self.assertTrue(result.success)
        self.assertEqual(target.read_text(), new_content)
        self.assertIsNotNone(result.backup_path)
        self.assertTrue(Path(result.backup_path).exists())

        # Verificar backup
        backup_content = Path(result.backup_path).read_text()
        self.assertEqual(backup_content, original)

    def test_write_append(self):
        """Testa modo append"""
        target = self.test_dir / "test.txt"
        line1 = "Line 1\n"
        line2 = "Line 2\n"

        # Criar arquivo
        target.write_text(line1)

        # Append
        result = self.writer.write_text(
            path=target,
            content=line2,
            mode=WriteMode.APPEND
        )

        self.assertTrue(result.success)
        self.assertEqual(target.read_text(), line1 + line2)

    def test_write_binary(self):
        """Testa escrita binária"""
        target = self.test_dir / "test.bin"
        content = b'\x00\x01\x02\x03'

        result = self.writer.write_bytes(
            path=target,
            content=content,
            mode=WriteMode.CREATE
        )

        self.assertTrue(result.success)
        self.assertEqual(target.read_bytes(), content)

    def test_write_create_fails_if_exists(self):
        """Testa que CREATE falha se arquivo existe"""
        target = self.test_dir / "test.txt"
        target.write_text("Existing")

        result = self.writer.write_text(
            path=target,
            content="New",
            mode=WriteMode.CREATE
        )

        self.assertFalse(result.success)
        self.assertIn("já existe", result.error_message)

    def test_dry_run_mode(self):
        """Testa modo dry-run"""
        writer_dry = SafeWriter(
            backup_dir=self.backup_dir,
            dry_run=True
        )

        target = self.test_dir / "test.txt"

        result = writer_dry.write_text(
            path=target,
            content="Content",
            mode=WriteMode.CREATE
        )

        self.assertTrue(result.success)
        self.assertFalse(target.exists())  # Não deve criar arquivo
        self.assertIn("DRY RUN", result.error_message)

    def test_get_backup_files(self):
        """Testa listagem de backups"""
        target = self.test_dir / "test.txt"

        # Criar e sobrescrever múltiplas vezes
        target.write_text("V1")
        self.writer.write_text(target, "V2", WriteMode.OVERWRITE)
        self.writer.write_text(target, "V3", WriteMode.OVERWRITE)

        backups = self.writer.get_backup_files(target)

        self.assertEqual(len(backups), 2)

    def test_restore_from_backup(self):
        """Testa restauração de backup"""
        target = self.test_dir / "test.txt"
        original = "Original"
        modified = "Modified"

        # Criar e modificar
        target.write_text(original)
        result = self.writer.write_text(target, modified, WriteMode.OVERWRITE)

        self.assertEqual(target.read_text(), modified)

        # Restaurar
        success = self.writer.restore_from_backup(
            backup_path=result.backup_path,
            target_path=target
        )

        self.assertTrue(success)
        self.assertEqual(target.read_text(), original)


if __name__ == '__main__':
    unittest.main()
