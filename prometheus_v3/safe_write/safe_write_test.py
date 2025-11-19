Safe Write Engine - Testes Unitários
"""

import unittest
import tempfile
import shutil
from pathlib import Path

from safe_write import SafeWriter, WriteOperation, WriteMode


class TestSafeWriter(unittest.TestCase):
    """
    Testes para SafeWriter
    """

    def setUp(self):
        """Setup antes de cada teste"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.backup_dir = self.test_dir / "backups"
        self.writer = SafeWriter(
            backup_dir=self.backup_dir,
            integrity_service=None,
            audit_logger=None,
            dry_run=False
        )

    def tearDown(self):
        """Cleanup após cada teste"""
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

    def test_write_overwrite_with_backup(self):
        """Testa sobrescrita com backup"""
        target = self.test_dir / "test.txt"
        original_content = "Original content"
        new_content = "New content"

        # Criar arquivo original
        target.write_text(original_content)

        # Sobrescrever
        result = self.writer.write_text(
            path=target,
            content=new_content,
            mode=WriteMode.OVERWRITE,
            create_backup=True
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.backup_path)
        self.assertTrue(Path(result.backup_path).exists())
        self.assertEqual(target.read_text(), new_content)

        # Verificar backup contém conteúdo original
        backup_content = Path(result.backup_path).read_text()
        self.assertEqual(backup_content, original_content)

    def test_write_append_mode(self):
        """Testa modo append"""
        target = self.test_dir / "test.txt"
        original = "Line 1\n"
        appended = "Line 2\n"

        # Criar arquivo original
        target.write_text(original)

        # Append
        result = self.writer.write_text(
            path=target,
            content=appended,
            mode=WriteMode.APPEND
        )

        self.assertTrue(result.success)
        self.assertEqual(target.read_text(), original + appended)

    def test_write_binary_file(self):
        """Testa escrita de arquivo binário"""
        target = self.test_dir / "test.bin"
        content = b'\x00\x01\x02\x03\x04\x05'

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

    def test_write_overwrite_fails_if_not_exists(self):
        """Testa que OVERWRITE falha se arquivo não existe"""
        target = self.test_dir / "nonexistent.txt"

        result = self.writer.write_text(
            path=target,
            content="Content",
            mode=WriteMode.OVERWRITE
        )

        self.assertFalse(result.success)
        self.assertIn("não existe", result.error_message)

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
        self.assertFalse(target.exists())  # Arquivo não deve ser criado
        self.assertIn("DRY RUN", result.error_message)

    def test_get_backup_files(self):
        """Testa listagem de backups"""
        target = self.test_dir / "test.txt"

        # Criar arquivo e fazer múltiplas sobrescritas
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

        # Restaurar backup
        success = self.writer.restore_from_backup(
            backup_path=result.backup_path,
            target_path=target
        )

        self.assertTrue(success)
        self.assertEqual(target.read_text(), original)


if __name__ == '__main__':
    unittest.main()
