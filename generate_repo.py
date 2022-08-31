"""
    Repository, addons.xml and addons.xml.md5 structural generator

        Modifications:

        - by Rodrigo@TVADDONS: Zip plugins/repositories to a "zip" folder
        - BartOtten: Create a repository addon, skip folders without addon.xml, user config file
        - Twilight0@TVADDONS: Ignore .idea subdirectories in addons' directories, changed from md5 module to hashlib
                              copy changelogs, icons and fanarts

    This file is provided "as is", without any warranty whatsoever. Use at your own risk
"""

from argparse import ArgumentParser
import glob
import hashlib
from io import TextIOWrapper, IOBase
import json
import os
import re
import shutil
import sys
from urllib.parse import urlparse
from xml.dom import minidom
from xml.dom.minidom import Node
import zipfile


# global variables
__PROGRAM_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))
CONFIG_FILE = os.path.join(__PROGRAM_DIR, 'config.json')
TEMPLATE_FILE = os.path.join(__PROGRAM_DIR, 'repo_addon.xml.tpl')


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Only handles single depth folder structure.
    """

    def __init__(self, config):
        self.config = config

        # create the output path
        if not os.path.exists(self.config.out_dir):
            os.makedirs(self.config.out_dir)

        # create repository addon path
        self.repo_addon_path = os.path.join(self.config.out_dir, self.config.addon_id)
        if not os.path.exists(self.repo_addon_path):
            os.makedirs(self.repo_addon_path)

        # generate files
        self._write_repo_addon_xml()
        self._generate_repo_addons_file()
        self._generate_addon_zip_files()

    def _write_repo_addon_xml(self):
        print("Create repository addon.xml")

        with open(TEMPLATE_FILE, "r") as f:
            template_xml = f.read()

        repo_xml = template_xml.format(
            addonid=self.config.addon_id,
            name=self.config.repo_name,
            version=self.config.version,
            author=self.config.author,
            summary=self.config.summary,
            description=self.config.description,
            url=self.config.url)

        # save file
        self._save_file(repo_xml, file_path=os.path.join(self.repo_addon_path, "addon.xml"))

    def _generate_addon_zip_files(self):
        # addon list
        addon_folders = self._listdir_full(self.config.in_dir)
        # add the repo addon
        addon_folders.append(self.repo_addon_path)

        # loop thru and add each addons addon.xml file
        for addon_folder in addon_folders:
            # create path
            addon_xml_path = os.path.join(addon_folder, "addon.xml")
            # skip path if it has no addon.xml
            if not os.path.isfile(addon_xml_path):
                continue
            try:
                # extract version and addon ID from the addon.xml
                version, addonid = self._get_addon_xml_tag(addon_xml_path, "version", "id")

                # zip the addon
                self._generate_zip_file(addon_folder, version, addonid)
            except Exception as e:
                print(e)

    def _generate_zip_file(self, addon_folder, version, addon_id):
        print("Generate zip file for " + addon_id + " " + version)

        # create output addon directory
        addon_out_path = os.path.join(self.config.out_dir, addon_id)
        if not os.path.exists(addon_out_path):
            os.makedirs(addon_out_path)

        # the path of the zip file
        zip_file_path = os.path.join(addon_out_path, addon_id + "-" + version + ".zip")

        try:
            # create the zip file
            zip_content = zipfile.ZipFile(zip_file_path, 'w', compression=zipfile.ZIP_DEFLATED)
            # fill it
            for current_root, dirs, files in os.walk(addon_folder):
                # ignore .svn and .git directories
                if '.svn' in dirs:
                    dirs.remove('.svn')
                if '.git' in dirs:
                    dirs.remove('.git')

                # write the current root folder
                rel_path = os.path.join(addon_id, os.path.relpath(current_root, addon_folder))
                zip_content.write(os.path.join(current_root), rel_path)

                # write the files in the current root folder
                for file in files:
                    # ignore dotfiles
                    if not file.startswith('.') and \
                            file != os.path.basename(zip_file_path):
                        rel_path = os.path.join(addon_id,
                                                os.path.relpath(os.path.join(current_root, file), addon_folder))
                        zip_content.write(os.path.join(current_root, file), rel_path)

            zip_content.close()
        except Exception as e:
            print(e)
        else:
            # create md5 file for the zip file
            self._create_md5_file(zip_file_path)

    def _generate_repo_addons_file(self):
        print("Generating addons.xml file")

        # addon list
        addon_folders = self._listdir_full(self.config.in_dir)
        # add the repo addon
        addon_folders.append(self.repo_addon_path)

        # addons.xml opening tags
        addons_xml_data = '<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n'

        # store the content of all addon.xml files
        addon_xml_files = {}

        # get the addon.xml from previous addon versions
        # these versions are present in the already zipped addons
        for existing_zip_file in glob.iglob(os.path.join(self.config.out_dir, "*", "*.zip")):
            try:
                with zipfile.ZipFile(existing_zip_file, 'r') as zip_fp:
                    # get the path of the compressed addon.xml file
                    compressed_addon_xml_path = [name
                                                 for name in zip_fp.namelist()
                                                 if re.match(r"^[^/]+/addon\.xml$", name)][0]

                    # read the addon.xml
                    with zip_fp.open(compressed_addon_xml_path, 'r') as compressed_addon_xml_fp:
                        # save the content of the existing addon.xml based on the addon ID and version
                        addon_xml_content = TextIOWrapper(compressed_addon_xml_fp)
                        addonid, version = self._get_addon_xml_tag(addon_xml_content, "id", "version")

                        if addonid in addon_xml_files:
                            addon_xml_files[addonid][version] = addon_xml_content.read().splitlines()
                        else:
                            addon_xml_files[addonid] = {version: addon_xml_content.read().splitlines()}
            except Exception as e:
                pass

        # loop through the addon directory and add each addons addon.xml file
        for addon_folder in addon_folders:
            try:
                # create path
                addon_xml_path = os.path.join(addon_folder, "addon.xml")
                # skip path if it has no addon.xml
                if not os.path.isfile(addon_xml_path):
                    continue

                with open(addon_xml_path, "r") as addon_xml_fp:
                    addonid, version = self._get_addon_xml_tag(addon_xml_fp, "id", "version")

                    # if the current identifier (addon ID and version) was already present, replace it
                    # otherwise add it
                    if (addonid in addon_xml_files and
                            version in addon_xml_files[addonid]):
                        addon_xml_files[addonid][version] = addon_xml_fp.read().splitlines()
                    else:
                        addon_xml_files[addonid] = {version: addon_xml_fp.read().splitlines()}
            except Exception:
                # poorly formatted addon.xml
                print("Excluding %s for %s" % (addon_xml_path, e))

        # iterate over all found addon.xml files
        for addon_versions in addon_xml_files.values():
            for addon_xml_lines in addon_versions.values():
                # new addon
                addon_xml_data = ""
                # loop thru cleaning each line
                for line in addon_xml_lines:
                    # skip encoding format line
                    if (line.find("<?xml") >= 0):
                        continue
                    # add line
                    addon_xml_data += line.rstrip() + "\n"
                # we succeeded so add to our final addons.xml text
                addons_xml_data += addon_xml_data.rstrip() + "\n\n"

        # clean and add closing tag
        addons_xml_data = addons_xml_data.strip() + "\n</addons>\n"

        addons_xml_path = os.path.join(self.config.out_dir, "addons.xml")
        # save file
        self._save_file(addons_xml_data, file_path=addons_xml_path)
        # create addons.xml.md5
        self._create_md5_file(addons_xml_path)

    def _create_md5_file(self, file_path):
        print(f"Generating {os.path.basename(file_path)}.md5 file")

        hash_md5 = hashlib.md5()

        try:
            # create a new md5 hash
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)

            # save file
            self._save_file(hash_md5.hexdigest(), file_path=file_path + ".md5")
        except Exception as e:
            # oops
            print(f"An error occurred creating {os.path.basename(file_path)}.md5 file!\n{e}")

    def _save_file(self, data, file_path):
        try:
            # write data to the file
            open(file_path, "w").write(data)
        except Exception as e:
            # oops
            print("An error occurred saving %s file!\n%s" % (file_path, e))

    def _get_addon_xml_tag(self, addon_xml_file_or_fp, *tags):
        # extract version and addon ID from the addon.xml
        parsed_xml = minidom.parse(addon_xml_file_or_fp)

        # reset file descriptor if it is one
        if isinstance(addon_xml_file_or_fp, IOBase):
            addon_xml_file_or_fp.seek(0)

        # the 'addon' tag is the parent
        for parent in parsed_xml.getElementsByTagName("addon"):
            if len(tags) == 1:
                # only return the single attribute
                return parent.getAttribute(tags[0])
            elif len(tags) > 1:
                # return multiple tags
                result = []
                for tag in tags:
                    result.append(parent.getAttribute(tag))
                return result

    def _listdir_full(self, directory):
        return [os.path.join(directory, f) for f in os.listdir(directory)]


class AssetCopier:
    def __init__(self, config):
        self.config = config

        # iterate over the addons
        addon_folders = os.listdir(self.config.in_dir)
        for addon_folder in addon_folders:
            addon_folder = os.path.join(self.config.in_dir, addon_folder)
            addon_xml_path = os.path.join(addon_folder, "addon.xml")
            if not os.path.isfile(addon_xml_path):
                continue

            addon_xml = minidom.parse(addon_xml_path)
            for parent in addon_xml.getElementsByTagName("addon"):
                addon_id = parent.getAttribute("id")
                addon_out_path = os.path.join(self.config.out_dir, addon_id)
                # a trailing slash is required by shutil.copy2 to preserve the file name at the destination
                addon_out_path = os.path.join(addon_out_path, '')

                # copy addon.xml
                shutil.copy2(addon_xml_path, addon_out_path)

                for extension in parent.getElementsByTagName("extension"):
                    if extension.getAttribute("point") != "xbmc.addon.metadata":
                        continue

                    # find the 'assets' tag
                    for assets in extension.getElementsByTagName("assets"):
                        # iterate over the assets
                        for asset in assets.childNodes:
                            # only process element nodes (<icon>, <fanart>, ...)
                            if asset.nodeType == Node.ELEMENT_NODE:
                                # the first child (Node.TEXT_NODE) of an asset element contains the path
                                shutil.copy2(os.path.join(addon_folder, asset.firstChild.nodeValue), addon_out_path)

                        # can exit here, because there is only one 'assets' tag
                        break


class Config:
    def __init__(self):
        # create the cli argument parser
        parser = self._init_parser()

        # get the settings from the config file
        config = self._read_config_file(CONFIG_FILE)

        # merge config file and cli arguments
        args = parser.parse_args()
        argparse_dict = vars(args)
        config.update({k: v for k, v in argparse_dict.items() if v})

        # check the config parameter
        self._validate_config(config)

        # add the config attributes to this instance
        for key, value in config.items():
            setattr(self, key, value)

        # save the config to file
        self._write_config_file(config, CONFIG_FILE)

    def _init_parser(self):
        parser = ArgumentParser(description="Create a Kodi repository")
        parser.add_argument('-n', '--name', metavar='Repository name', type=str, dest='repo_name',
                            help="The name of the repository")
        parser.add_argument('-r', '--id', metavar='Repository addon ID', type=str, dest='addon_id',
                            help="The ID of the repository addon (must start with 'repository.')")
        parser.add_argument('-v', '--version', metavar='Version', type=str, dest='version',
                            help="The version of the repository addon")
        parser.add_argument('-a', '--author', metavar='Author', type=str, dest='author',
                            help="The author of the repository")
        parser.add_argument('-s', '--summary', metavar='Summary', type=str, dest='summary',
                            help="A short summary of this repository")
        parser.add_argument('-d', '--description', metavar='Description', type=str, dest='description',
                            help=("The description can be longer. Using [CR] you can create a newline. ",
                                  "The use of other markup is not advised."))
        parser.add_argument('-u', '--url', metavar='Remote repository URL', type=str, dest='url',
                            help=("The later URL of the repository main directory, e.g. ",
                                  "https://raw.githubusercontent.com/Your-Github-Username/repository-link/"))
        parser.add_argument('-i', '--input-dir', metavar='Input directory', type=str, dest='in_dir',
                            help="The directory containing the addons that should be added to the repository")
        parser.add_argument('-o', '--output-dir', metavar='Output directory', type=str, dest='out_dir',
                            help="The output directory of the repository")

        return parser

    def _validate_config(self, config):
        # check for missing and wrong settings
        missing_args = []
        wrong_args = []
        if not config['repo_name']:
            missing_args.append("--name")
        if not config['addon_id']:
            missing_args.append("--id")
        elif not config['addon_id'].startswith('repository.'):
            wrong_args.append("--id: The addon ID must start with 'repository.'")
        if not config['version']:
            missing_args.append("--version")
        if not config['author']:
            missing_args.append("--author")
        if not config['summary']:
            missing_args.append("--summary")
        if not config['description']:
            missing_args.append("--description")
        if not config['url']:
            missing_args.append("--url")
        else:
            # remove trailing slash if it's there
            if config['url'].endswith('/'):
                config['url'] = config['url'][:-1]

            # check for a valid URL
            parsed_url = urlparse(config['url'])
            if not parsed_url.scheme or \
                    not parsed_url.netloc:
                wrong_args.append("--url: a valid URL must be provided")
        if not config['in_dir']:
            missing_args.append("--input-dir")
        else:
            if not os.path.isdir(config['in_dir']):
                wrong_args.append("--input-dir: a valid directory must be provided")
        if not config['out_dir']:
            missing_args.append("--output-dir")
        # if the output directory does not exist, it will be created later

        if missing_args:
            print('the following arguments are required:\n\t%s' % '\n\t'.join(missing_args),
                  file=sys.stderr)
            sys.exit(1)
        if wrong_args:
            print('there were errors with the following arguments:\n\t%s' % '\n\t'.join(wrong_args),
                  file=sys.stderr)
            sys.exit(1)

    def _read_config_file(self, file_path):
        # check if a config file exists
        if not os.path.isfile(file_path):
            # create a new one if no config file exists
            with open(file_path, 'w') as f:
                json.dump({}, f)

        # load the config file
        with open(file_path, 'r') as f:
            try:
                config = json.load(f)
            except Exception:
                config = {}

        # return the content of the config file as dict
        return config

    def _write_config_file(self, config, file_path):
        # write the config to file
        with open(file_path, 'w') as f:
            json.dump(config, f, sort_keys=True, indent=4)


if __name__ == "__main__":
    # load the config
    config = Config()

    Generator(config)
    AssetCopier(config)
    print("Finished updating addons xml & md5 files, zipping addons and copying additional files")
