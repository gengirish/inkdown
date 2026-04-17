import os
import subprocess
import tempfile
import unittest


class TestMd2Pdf(unittest.TestCase):
    def run_converter(self, args):
        result = subprocess.run(
            ["python3", os.path.join(os.path.dirname(__file__), "..", "md2pdf.py")] + args,
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Command failed: {result.args}\nstdout: {result.stdout}\nstderr: {result.stderr}"
            )
        return result

    def test_fpdf_backend_file_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = os.path.join(temp_dir, "test.md")
            pdf_path = os.path.join(temp_dir, "test.pdf")
            with open(markdown_path, "w", encoding="utf-8") as handle:
                handle.write("# Test\n\nThis is **bold** and *italic* text.\n")

            self.run_converter(["--backend", "fpdf", markdown_path, pdf_path])
            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)

    def test_auto_backend_stdout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            markdown_path = os.path.join(temp_dir, "test.md")
            pdf_path = os.path.join(temp_dir, "stdout.pdf")
            with open(markdown_path, "w", encoding="utf-8") as handle:
                handle.write("# Stream Test\n\n`inline code` sample.\n")

            result = subprocess.run(
                ["python3", os.path.join(os.path.dirname(__file__), "..", "md2pdf.py"), "--backend", "auto", markdown_path, "-"],
                cwd=os.path.dirname(__file__),
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8"))
            with open(pdf_path, "wb") as handle:
                handle.write(result.stdout)

            self.assertTrue(os.path.exists(pdf_path))
            self.assertGreater(os.path.getsize(pdf_path), 0)


if __name__ == "__main__":
    unittest.main()
