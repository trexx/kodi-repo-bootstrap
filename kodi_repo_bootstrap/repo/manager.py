from itertools import chain
import shutil
from pathlib import Path
from typing import Dict, Iterator, List, Tuple

from kodi_repo_bootstrap.addon.addon import Addon, RepoAddon
from kodi_repo_bootstrap.addon.manager import AddonManager
from kodi_repo_bootstrap.fs.dir import Directory
from kodi_repo_bootstrap.fs.file import File
from kodi_repo_bootstrap.repo.config import Config
from kodi_repo_bootstrap.repo.version import SemanticVersion


class RepoManager:
    def __init__(self, config: Config) -> None:
        self.__config: Config = config

        self.__addons_manager: AddonManager = AddonManager(addons_dir=config.addons_dir,
                                                           repo_dir=config.repo_dir)

        self.__repo_addon: RepoAddon = RepoAddon(config)

        # create addon directories for output in repo_dir
        self.__addons_not_in_repo_with_out_path: List[Tuple[Addon, Path]] = []
        addon: Addon
        for addon in self.__addons_manager.get_addons_not_in_repo():
            addon_out_path: Path = self.__config.repo_dir / addon.id
            addon_out_path.mkdir(exist_ok=True)

            # save for later use
            self.__addons_not_in_repo_with_out_path.append((addon, addon_out_path))

    def create_repo_addons_xml(self) -> None:
        print("Generating addons.xml file")

        # addons.xml opening tags
        addons_xml_data: str = '<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n'

        # store the content of all addon.xml files
        addon_xml_files: Dict[str, Dict[SemanticVersion, List[str]]] = {}

        # get the addon.xml from the new and previous addon versions
        addon: Addon
        for addon in self.__addons_manager.get_all_addons():
            if addon.id in addon_xml_files:
                addon_xml_files[addon.id][addon.version] = addon.addon_xml_lines
            else:
                addon_xml_files[addon.id] = {addon.version: addon.addon_xml_lines}

        # iterate over all found addon.xml files
        addon_versions: Dict[SemanticVersion, List[str]]
        for addon_versions in addon_xml_files.values():
            addon_xml_lines: List[str]
            for addon_xml_lines in addon_versions.values():
                # new addon
                addon_xml_data: str = ""
                # loop thru cleaning each line
                line: str
                for line in addon_xml_lines:
                    # skip encoding format line
                    if line.find("<?xml") >= 0:
                        continue

                    # add line
                    addon_xml_data += line.rstrip() + "\n"

                # we succeeded so add to our final addons.xml text
                addons_xml_data += addon_xml_data.rstrip() + "\n\n"

        # clean and add closing tag
        addons_xml_data = addons_xml_data.strip() + "\n</addons>\n"

        addons_xml_path: Path = self.__config.repo_dir / "addons.xml"

        # save file
        File.save_file(addons_xml_data, file_path=addons_xml_path)

        # create addons.xml.md5
        File.create_md5_file(addons_xml_path)

    def copy_addon_assets_to_repo(self) -> None:
        # get the addon ZIP and their corresponding md5 files
        # (for excluding them later from being deleted)
        previous_addon_zip_md5_files: Iterator[str] = chain.from_iterable(
            chain((a.addon_path.name, f"{a.addon_path.name}.md5"))
                for a in self.__addons_manager.get_addons_in_repo()
        )

        # iterate over the addon directories
        addon: Addon
        addon_out_path: Path
        for addon, addon_out_path in self.__addons_not_in_repo_with_out_path:
            # first clear the destination directory
            # only keep any previous addon ZIP and their corresponding md5 files
            path_to_delete: Path
            for path_to_delete in Directory.multi_glob_exclude(addon_out_path, *previous_addon_zip_md5_files):
                if path_to_delete.is_dir() and not path_to_delete.is_symlink():
                    shutil.rmtree(path_to_delete)
                else:
                    path_to_delete.unlink()

            addon.copy_assets_to_dir(dest_dir=addon_out_path)

    def create_addon_zip_files(self) -> None:
        # create repo addon zip file
        self.__repo_addon.create_zip_file()

        # create the zip files for all other addons
        addon: Addon
        addon_out_path: Path
        for addon, addon_out_path in self.__addons_not_in_repo_with_out_path:
            addon.create_zip_file(dest_dir=addon_out_path)
