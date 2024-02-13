from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, Final, Tuple, final


@final
class CLIArgsMeta:
    CONFIG_FILE_ARG: Final[str] = "config_file"

    REPO_NAME_ARG: Final[Tuple[str, str]] = ("-n", "--name")
    REPO_ADDON_ID_ARG: Final[Tuple[str, str]] = ("-r", "--id")
    REPO_ADDON_VERSION_ARG: Final[Tuple[str, str]] = ("-v", "--version")
    REPO_ADDON_AUTOR_ARG: Final[Tuple[str, str]] = ("-a", "--author")
    REPO_ADDON_SUMMARY_ARG: Final[Tuple[str, str]] = ("-s", "--summary")
    REPO_ADDON_DESCRIPTION_ARG: Final[Tuple[str, str]] = ("-d", "--description")
    REPO_URL_ARG: Final[Tuple[str, str]] = ("-u", "--url")
    ADDONS_DIR_ARG: Final[Tuple[str, str]] = ("-i", "--addons-dir")
    REPO_DIR_ARG: Final[Tuple[str, str]] = ("-o", "--repo-dir")


class CLIArgs:
    def __init__(self) -> None:
        parser: ArgumentParser = self.__init_parser()
        self.__args: Namespace = parser.parse_args()

    def __init_parser(self) -> ArgumentParser:
        parser: ArgumentParser = ArgumentParser(description="Create a Kodi repository")

        parser.add_argument(*CLIArgsMeta.REPO_NAME_ARG, metavar='Repository name', type=str, dest='repo_name',
                            help="The name of the repository")
        parser.add_argument(*CLIArgsMeta.REPO_ADDON_ID_ARG, metavar='Repository addon ID', type=str,
                            dest='repo_addon_id',
                            help="The ID of the repository addon (must start with 'repository.')")
        parser.add_argument(*CLIArgsMeta.REPO_ADDON_VERSION_ARG, metavar='Version', type=str, dest='repo_addon_version',
                            help="The version of the repository addon")
        parser.add_argument(*CLIArgsMeta.REPO_ADDON_AUTOR_ARG, metavar='Author', type=str, dest='repo_addon_author',
                            help="The author of the repository")
        parser.add_argument(*CLIArgsMeta.REPO_ADDON_SUMMARY_ARG, metavar='Summary', type=str, dest='repo_addon_summary',
                            help="A short summary of this repository")
        parser.add_argument(*CLIArgsMeta.REPO_ADDON_DESCRIPTION_ARG, metavar='Description', type=str,
                            dest='repo_addon_description',
                            help=("The description can be longer. Using [CR] you can create a newline. "
                                  "The use of other markup is not advised."))
        parser.add_argument(*CLIArgsMeta.REPO_URL_ARG, metavar='Remote repository URL', type=str, dest='repo_url',
                            help=("The later URL of the repository main directory, e.g. "
                                  "https://raw.githubusercontent.com/Your-Github-Username/repository-link/"))
        parser.add_argument(*CLIArgsMeta.ADDONS_DIR_ARG, metavar='Addons directory', type=Path, dest='addons_dir',
                            help="The parent directory containing the addons that should be added to the repository")
        parser.add_argument(*CLIArgsMeta.REPO_DIR_ARG, metavar='Repository directory', type=Path, dest='repo_dir',
                            help="The output directory of the new Kodi repository")

        parser.add_argument(CLIArgsMeta.CONFIG_FILE_ARG, metavar=CLIArgsMeta.CONFIG_FILE_ARG.upper(), type=Path,
                            help="The configuration file")

        return parser

    def get_args(self) -> Dict[str, Any]:
        return vars(self.__args)
