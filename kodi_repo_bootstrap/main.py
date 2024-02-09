from kodi_repo_bootstrap.repo.config import Config, ConfigFile
from kodi_repo_bootstrap.repo.manager import RepoManager


def run() -> None:
    # load configuration
    config_file: ConfigFile = ConfigFile()
    config: Config = config_file.get_config()

    # create the Kodi repository
    repo_manager: RepoManager = RepoManager(config)
    repo_manager.create_repo_addons_xml()
    repo_manager.copy_addon_assets_to_repo()
    repo_manager.create_addon_zip_files()
