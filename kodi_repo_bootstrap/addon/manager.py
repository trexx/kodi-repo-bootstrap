from itertools import chain
from pathlib import Path
from typing import Dict, Iterator
from zipfile import BadZipFile

from kodi_repo_bootstrap.addon.addon import Addon
from kodi_repo_bootstrap.fs.dir import Directory


class AddonManager:
    def __init__(self, addons_dir: Path, repo_dir: Path) -> None:
        self.__addons_dir: Path = addons_dir
        self.__repo_dir: Path = repo_dir

        # this dict should only contain the latest version of an addon
        self.__addons_latest_version: Dict[str, Addon] = {}

    def __glob_addon(self, root_dir: Path, *glob_patterns: str) -> Iterator[Addon]:
        if not root_dir.is_dir():
            raise ValueError(f"'{root_dir}' is not an existing directory.")

        found_file: Path
        for found_file in Directory.multi_glob(root_dir, *glob_patterns):
            try:
                if found_file.suffix == ".xml":
                    yield Addon(addon_path=found_file.parent)
                else:
                    yield Addon(addon_path=found_file)
            except (ValueError, BadZipFile) as e:
                print(f"Skipping addon path '{found_file}'")
                print(f"\t{str(e)}")

    def get_addons_not_in_repo(self) -> Iterator[Addon]:
        if not self.__addons_latest_version:
            # iterate over all addons in the addons_dir
            cur_addon: Addon
            for cur_addon in self.__glob_addon(self.__addons_dir,
                                               # valid directory structure for the new addons:
                                               # addons_dir/
                                               #     |- plugin.addon.id-versionX.zip
                                               #     - and / or -
                                               #     |- plugin.addon.id/
                                               #     |    |- addon.xml
                                               #     |    |- ...
                                               #     |    - and / or -
                                               #     |    |- plugin.addon.id-versionX.zip
                                               "*.zip", "*/addon.xml", "*/*.zip"):
                # check if the addon is already known
                if cur_addon.id in self.__addons_latest_version:
                    # compare the version
                    if cur_addon.version > self.__addons_latest_version[cur_addon.id].version:
                        # the current addon version is newer, save it in the dict
                        self.__addons_latest_version[cur_addon.id] = cur_addon
                    else:
                        print(f"Skipping addon '{cur_addon.addon_path}', "
                              "because a newer version is present in addons_dir.")
                else:
                    # add the current addon to the dict, because it's not known
                    self.__addons_latest_version[cur_addon.id] = cur_addon

        return iter(self.__addons_latest_version.values())

    def get_addons_in_repo(self) -> Iterator[Addon]:
        return self.__glob_addon(self.__repo_dir,
                                 # valid directory structure for the existing addons (already in the repo):
                                 # repo_dir/
                                 #    |- plugin.addon.id/
                                 #    |    |- plugin.addon.id-versionX.zip
                                 "*/*.zip")

    def get_all_addons(self) -> Iterator[Addon]:
        return chain(self.get_addons_not_in_repo(), self.get_addons_in_repo())
