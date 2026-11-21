"""Inspect Python sources without running submission code."""

import ast
import zlib
from io import BytesIO
from pathlib import PurePosixPath
from typing import Literal
from zipfile import ZIP_DEFLATED, ZIP_STORED, BadZipFile, ZipFile


BuildStatus = Literal["passed", "failed"]
MAX_SOURCE_BYTES = 512 * 1024
MAX_ZIP_ENTRIES = 256


def check_artifact(filename: str, content: bytes) -> tuple[BuildStatus, str]:
    if not content:
        return "failed", "Загруженный файл пуст."
    extension = PurePosixPath(filename).suffix.lower()
    if extension == ".py":
        return check_python(filename, content)
    if extension != ".zip":
        return "failed", "Поддерживаются файлы .py и архивы .zip с Python-проектом."

    try:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ZIP_ENTRIES:
                return "failed", "В ZIP должно быть не более 256 записей."
            candidates = []
            for entry in entries:
                path = PurePosixPath(entry.filename)
                if entry.is_dir() or path.is_absolute() or {"..", "__MACOSX"}.intersection(path.parts):
                    continue
                if path.name in {"main.py", "__main__.py"}:
                    candidates.append((path, entry))
            if not candidates:
                return "failed", "В ZIP не найден main.py или __main__.py."
            path, entry = min(candidates, key=lambda item: (len(item[0].parts), str(item[0])))
            if entry.compress_type not in {ZIP_STORED, ZIP_DEFLATED}:
                return "failed", "Для файла в ZIP поддерживаются методы STORE и DEFLATE."
            if entry.file_size > MAX_SOURCE_BYTES:
                return "failed", "Размер входного файла Python превышает 512 КиБ."
            with archive.open(entry) as source:
                return check_python(str(path), source.read(MAX_SOURCE_BYTES + 1))
    except (BadZipFile, EOFError, OSError, RuntimeError, ValueError, zlib.error):
        return "failed", "ZIP повреждён или его входной файл не удалось прочитать."


def check_python(filename: str, source: bytes) -> tuple[BuildStatus, str]:
    if len(source) > MAX_SOURCE_BYTES:
        return "failed", "Размер входного файла Python превышает 512 КиБ."
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as error:
        location = f", строка {error.lineno}" if error.lineno else ""
        return "failed", f"{filename}{location}: {error.msg}."
    except (ValueError, RecursionError):
        return "failed", f"{filename}: не удалось разобрать исходный код."
    if not tree.body:
        return "failed", f"{filename}: в файле нет кода."
    return "passed", f"{filename}: синтаксис Python корректен."
