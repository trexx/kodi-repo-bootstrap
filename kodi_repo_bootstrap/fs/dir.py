import fnmatch
import re
from itertools import chain
from pathlib import Path
from re import Pattern
from typing import Iterator


class Directory:
    @classmethod
    def multi_glob(cls, root_dir: Path, *glob_patterns: str) -> Iterator[Path]:
        if not root_dir.is_dir():
            raise ValueError(f"'{root_dir}' must be a directory")

        path_elem: Path
        for path_elem in chain.from_iterable(root_dir.glob(p) for p in glob_patterns):
            yield path_elem

    @classmethod
    def multi_glob_exclude(cls, root_dir: Path, *glob_patterns) -> Iterator[Path]:
        if not root_dir.is_dir():
            raise ValueError(f"'{root_dir}' must be a directory")

        pattern: Pattern = re.compile("|".join(fnmatch.translate(p) for p in glob_patterns))

        path_elem: Path
        for path_elem in root_dir.glob("**/*"):
            if not pattern.match(str(path_elem.relative_to(root_dir))):
                yield path_elem
