import unittest
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile

from analysis.checker import MAX_SOURCE_BYTES, MAX_ZIP_ENTRIES, check_artifact


def zip_project(files: dict[str, bytes]) -> bytes:
    target = BytesIO()
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path, content in files.items():
            archive.writestr(path, content)
    return target.getvalue()


class CheckerTests(unittest.TestCase):
    def test_python_is_parsed_without_running_it(self):
        status, _ = check_artifact("task.py", b"raise RuntimeError('must never execute')\n")
        self.assertEqual(status, "passed")

    def test_python_syntax_error_explains_the_line(self):
        status, details = check_artifact("task.py", b"print(1)\nif:\n")
        self.assertEqual(status, "failed")
        self.assertIn("строка 2", details)

    def test_empty_comment_only_and_unsupported_files_fail(self):
        for filename, content in [("a.py", b""), ("a.py", b"# only a comment\n"), ("readme.txt", b"text")]:
            with self.subTest(filename=filename, content=content):
                self.assertEqual(check_artifact(filename, content)[0], "failed")

    def test_zip_selects_shallowest_entrypoint(self):
        artifact = zip_project({"repo/pkg/main.py": b"if:", "repo/__main__.py": b"print(1)"})
        status, details = check_artifact("project.zip", artifact)
        self.assertEqual(status, "passed")
        self.assertIn("repo/__main__.py", details)

    def test_zip_with_only_readme_or_invalid_entrypoint_fails(self):
        for files in [{"README.md": b"# project"}, {"main.py": b"if:"}, {}]:
            with self.subTest(files=files):
                self.assertEqual(check_artifact("project.zip", zip_project(files))[0], "failed")
        self.assertEqual(check_artifact("project.zip", b"not a zip")[0], "failed")

    def test_zip_limits_entry_count_and_uncompressed_source(self):
        files = {f"entry_{number}.txt": b"" for number in range(MAX_ZIP_ENTRIES)}
        files["main.py"] = b"print(1)"
        self.assertEqual(check_artifact("project.zip", zip_project(files))[0], "failed")
        oversized = zip_project({"main.py": b"#" * (MAX_SOURCE_BYTES + 1)})
        self.assertEqual(check_artifact("project.zip", oversized)[0], "failed")
