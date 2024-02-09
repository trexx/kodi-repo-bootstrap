import hashlib
from pathlib import Path
from typing import Final

DEFAULT_FILE_ENCODING: Final[str] = "utf-8"


class File:
    @classmethod
    def create_md5_file(cls, original_file_path: Path) -> None:
        md5_file_path: Path = original_file_path.with_name(original_file_path.name + ".md5")
        print(f"Generating {md5_file_path.name} file")

        hash_md5 = hashlib.md5()

        # create a new md5 hash
        with open(original_file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)

        # save file
        cls.save_file(hash_md5.hexdigest(), file_path=md5_file_path)

    @classmethod
    def save_file(cls, data: str, file_path: Path) -> None:
        try:
            # write data to the file
            with open(file_path, "w", encoding=DEFAULT_FILE_ENCODING) as f:
                f.write(data)
        except OSError as e:
            # oops
            print(f"An error occurred writing {file_path} file!\n{e}")
