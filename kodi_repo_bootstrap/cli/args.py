from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Any, Dict, Tuple, final


@final
class CLIArgsMeta:
    repo_name_arg: Tuple[str, str] = ("-n", "--name")
    repo_addon_id_arg: Tuple[str, str] = ("-r", "--id")
    repo_addon_version_arg: Tuple[str, str] = ("-v", "--version")
    repo_addon_author_arg: Tuple[str, str] = ("-a", "--author")
    repo_addon_summary_arg: Tuple[str, str] = ("-s", "--summary")
    repo_addon_description_arg: Tuple[str, str] = ("-d", "--description")
    repo_url_arg: Tuple[str, str] = ("-u", "--url")
    addons_dir_arg: Tuple[str, str] = ("-i", "--addons-dir")
    repo_dir_arg: Tuple[str, str] = ("-o", "--repo-dir")


class CLIArgs:
    def __init__(self) -> None:
        parser: ArgumentParser = self.__init_parser()
        self.__args: Namespace = parser.parse_args()

    def __init_parser(self) -> ArgumentParser:
        parser: ArgumentParser = ArgumentParser(description="Create a Kodi repository")

        parser.add_argument(*CLIArgsMeta.repo_name_arg, metavar='Repository name', type=str, dest='repo_name',
                            help="The name of the repository")
        parser.add_argument(*CLIArgsMeta.repo_addon_id_arg, metavar='Repository addon ID', type=str,
                            dest='repo_addon_id',
                            help="The ID of the repository addon (must start with 'repository.')")
        parser.add_argument(*CLIArgsMeta.repo_addon_version_arg, metavar='Version', type=str, dest='repo_addon_version',
                            help="The version of the repository addon")
        parser.add_argument(*CLIArgsMeta.repo_addon_author_arg, metavar='Author', type=str, dest='repo_addon_author',
                            help="The author of the repository")
        parser.add_argument(*CLIArgsMeta.repo_addon_summary_arg, metavar='Summary', type=str, dest='repo_addon_summary',
                            help="A short summary of this repository")
        parser.add_argument(*CLIArgsMeta.repo_addon_description_arg, metavar='Description', type=str,
                            dest='repo_addon_description',
                            help=("The description can be longer. Using [CR] you can create a newline. "
                                  "The use of other markup is not advised."))
        parser.add_argument(*CLIArgsMeta.repo_url_arg, metavar='Remote repository URL', type=str, dest='repo_url',
                            help=("The later URL of the repository main directory, e.g. "
                                  "https://raw.githubusercontent.com/Your-Github-Username/repository-link/"))
        parser.add_argument(*CLIArgsMeta.addons_dir_arg, metavar='Addons directory', type=Path, dest='addons_dir',
                            help="The parent directory containing the addons that should be added to the repository")
        parser.add_argument(*CLIArgsMeta.repo_dir_arg, metavar='Repository directory', type=Path, dest='repo_dir',
                            help="The output directory of the new Kodi repository")

        parser.add_argument("config_file", metavar="CONFIG_FILE", type=Path,
                            help="The configuration file")

        return parser

    def get_args(self) -> Dict[str, Any]:
        return vars(self.__args)
