import dataclasses
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, cast
from urllib.parse import ParseResult, urlparse

from kodi_repo_bootstrap.cli.args import CLIArgs, CLIArgsMeta
from kodi_repo_bootstrap.fs.file import DEFAULT_FILE_ENCODING


@dataclass
class Config:
    repo_name: str
    repo_addon_id: str
    repo_addon_version: str
    repo_addon_author: str
    repo_addon_summary: str
    repo_addon_description: str
    repo_url: str
    addons_dir: Path
    repo_dir: Path

    def __post_init__(self) -> None:
        if self.addons_dir is not None:
            self.addons_dir = Path(self.addons_dir).resolve(strict=True)
        if self.repo_dir is not None:
            self.repo_dir = Path(self.repo_dir).resolve(strict=True)

        self.__validate()

    def __validate(self) -> None:
        # check for missing and wrong settings
        missing_args: List[str] = []
        wrong_args: List[str] = []

        if not self.repo_name:
            missing_args.append(CLIArgsMeta.REPO_NAME_ARG[1])
        if not self.repo_addon_id:
            missing_args.append(CLIArgsMeta.REPO_ADDON_ID_ARG[1])
        elif not self.repo_addon_id.startswith("repository."):
            wrong_args.append(f"{CLIArgsMeta.REPO_ADDON_ID_ARG[1]}: The addon ID must start with 'repository.'")
        if not self.repo_addon_version:
            missing_args.append(CLIArgsMeta.REPO_ADDON_VERSION_ARG[1])
        if not self.repo_addon_author:
            missing_args.append(CLIArgsMeta.REPO_ADDON_AUTOR_ARG[1])
        if not self.repo_addon_summary:
            missing_args.append(CLIArgsMeta.REPO_ADDON_SUMMARY_ARG[1])
        if not self.repo_addon_description:
            missing_args.append(CLIArgsMeta.REPO_ADDON_DESCRIPTION_ARG[1])
        if not self.repo_url:
            missing_args.append(CLIArgsMeta.REPO_URL_ARG[1])
        else:
            # remove trailing slash if it's there
            if self.repo_url.endswith('/'):
                self.repo_url = self.repo_url[:-1]

            # check for a valid URL
            parsed_url: ParseResult = urlparse(self.repo_url)
            if not parsed_url.scheme or \
                    not parsed_url.netloc:
                wrong_args.append(f"{CLIArgsMeta.REPO_URL_ARG[1]}: a valid URL must be provided")
        if not self.addons_dir:
            missing_args.append(CLIArgsMeta.ADDONS_DIR_ARG[1])
        else:
            if not self.addons_dir.is_dir():
                wrong_args.append(f"{CLIArgsMeta.ADDONS_DIR_ARG[1]}: a valid directory must be provided")
        if not self.repo_dir:
            missing_args.append(CLIArgsMeta.REPO_DIR_ARG[1])
        # if the repo directory does not exist, it will be created later

        if missing_args:
            print("The following arguments are required:\n\t%s" % "\n\t".join(missing_args),
                  file=sys.stderr)
            raise ValueError
        if wrong_args:
            print("There were errors with the following arguments:\n\t%s" % "\n\t".join(wrong_args),
                  file=sys.stderr)
            raise ValueError

    def as_dict(self) -> Dict[str, Optional[str]]:
        return {
            field.name: str(getattr(self, field.name))
                            if getattr(self, field.name) is not None
                        else None
            for field in dataclasses.fields(self)
        }


class ConfigFile:
    def __init__(self):
        # get the config from the CLI arguments
        config_dict: Dict[str, Any] = CLIArgs().get_args()

        self.__config_file: Path = cast(Path, config_dict.pop(CLIArgsMeta.CONFIG_FILE_ARG)).resolve()

        # get the settings from the config file
        config_dict_from_file: Dict[str, Any] = self.__read_config_file(self.__config_file)

        # merge config file and cli arguments
        config_dict_from_file.update({k: v for k, v in config_dict.items() if v})

        # create the Config object
        self.__config: Config = Config(**config_dict_from_file)

        # save the config to file
        self.__write_config_file(self.__config)

    def __read_config_file(self, file_path: Path) -> Dict[str, Any]:
        # check if a config file exists
        if not file_path.is_file():
            # create a new one if no config file exists
            with open(file_path, 'w', encoding=DEFAULT_FILE_ENCODING) as f:
                json.dump({}, f)

        # load the config file
        loaded_config: Dict[str, Any]
        with open(file_path, 'r', encoding=DEFAULT_FILE_ENCODING) as f:
            try:
                loaded_config = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Error parsing the config file. Assuming empty config.")
                loaded_config = {}

        # return the content of the config file as dict
        return loaded_config

    def __write_config_file(self, config: Config) -> None:
        # write the config to file
        with open(self.__config_file, 'w', encoding=DEFAULT_FILE_ENCODING) as f:
            json.dump(config.as_dict(), f, sort_keys=True, indent=4)

    def get_config(self) -> Config:
        return self.__config
