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
import fnmatch
import hashlib
import json
import os
import re
import shutil
import sys
from urllib.parse import urlparse
from xml.dom import minidom
import zipfile


# global variables
CONFIG_FILE = 'config.json'
TEMPLATE_FILE = 'template.xml'

# Load the configuration:
tools_path = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__))))


class Generator:
    """
        Generates a new addons.xml file from each addons addon.xml file
        and a new addons.xml.md5 hash file. Must be run from a subdirectory (eg. _tools) of
        the checked-out repo. Only handles single depth folder structure.
    """

    def __init__(self, config):
        self.config = config
        
        # create the addon repository path
        if not os.path.exists(self.config.repo_path):
            os.makedirs(self.config.repo_path)
        
        # the repository xml file
        self.repo_xml_file = os.path.join(self.config.repo_path, "addon.xml")

        # generate files
        self._write_repo_addon_xml()
        self._generate_repo_zip_file()
        self._generate_repo_addons_file()
        self._generate_repo_addons_md5_file()
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
        self._save_file(repo_xml, file=self.repo_xml_file)

    def _generate_addon_zip_files(self):
        # addon list
        addon_folders = os.listdir(self.config.in_dir)
        
        # loop thru and add each addons addon.xml file
        for addon_folder in addon_folders:
            # create path
            addon_xml_path = os.path.join(self.config.in_dir, addon_folder, "addon.xml")
            # skip path if it has no addon.xml
            if not os.path.isfile(addon_xml_path):
                continue
            try:
                # extract version and addon ID from the addon.xml
                addon_xml = minidom.parse(addon_xml_path)
                for parent in addon_xml.getElementsByTagName("addon"):
                    version = parent.getAttribute("version")
                    addonid = parent.getAttribute("id")
                
                # zip the addon
                self._generate_zip_file(addon_folder, version, addonid)
            except Exception as e:
                print(e)

    def _generate_zip_file(self, folder_name, version, addon_id):
        print("Generate zip file for " + addon_id + " " + version)
        
        # create output addon directory
        addon_out_path = os.path.join(self.config.repo_path, addon_id)
        if not os.path.exists(addon_out_path):
            os.makedirs(addon_out_path)
        
        # the path of the zip file
        zip_file = os.path.join(addon_out_path, addon_id + "-" + version + ".zip")
        
        try:
            # the root path of the addon
            root = os.path.join(self.config.in_dir, folder_name)
            
            # create the zip file
            zip_content = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
            # fill it
            for current_root, dirs, files in os.walk(root):
                # ignore .svn and .git directories
                if '.svn' in dirs:
                    dirs.remove('.svn')
                if '.git' in dirs:
                    dirs.remove('.git')
                
                # write the current root folder
                rel_path = os.path.join(addon_id, os.path.relpath(os.path.join(current_root), os.path.join(root)))
                zip_content.write(os.path.join(current_root), rel_path)
                
                # write the files in the current root folder
                for file in files:
                    # ignore dotfiles
                    if not file.startswith('.'):
                        rel_path = os.path.join(addon_id, os.path.relpath(os.path.join(current_root, file), os.path.join(root)))
                        zip_content.write(os.path.join(current_root, file), rel_path)

            zip_content.close()
        except Exception as e:
            print(e)
    
    def _generate_repo_zip_file(self):
        print("Generate zip file for " + self.config.addon_id + " " + self.config.version)
        
        # the path of the zip file
        zip_file = os.path.join(self.config.repo_path, self.config.addon_id + "-" + self.config.version + ".zip")
        
        try:
            # create the zip file
            zip_content = zipfile.ZipFile(zip_file, 'w', compression=zipfile.ZIP_DEFLATED)
            # write the root folder
            zip_content.write(os.path.join(self.config.repo_path), self.config.addon_id)
            # add the addon.xml
            zip_content.write(self.repo_xml_file, os.path.join(self.config.addon_id, os.path.basename(self.repo_xml_file)))
            
            zip_content.close()
        except Exception as e:
            print(e)

    def _generate_repo_addons_file(self):
        print("Generating addons.xml file")
        
        # addon list
        addon_folders = os.listdir(self.config.in_dir)
        
        # addons.xml opening tags
        addons_xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<addons>\n"
        
        # loop thru and add each addons addon.xml file
        for addon_folder in addon_folders:
            # create path
            addon_xml_path = os.path.join(self.config.in_dir, addon_folder, "addon.xml")
            # skip path if it has no addon.xml
            if not os.path.isfile(addon_xml_path):
                continue
            try:
                # split lines for stripping
                xml_lines = open(addon_xml_path, "r").read().splitlines()
                # new addon
                addon_xml = ""
                # loop thru cleaning each line
                for line in xml_lines:
                    # skip encoding format line
                    if (line.find("<?xml") >= 0):
                        continue
                    # add line
                    addon_xml += line.rstrip() + "\n"
                # we succeeded so add to our final addons.xml text
                addons_xml += addon_xml.rstrip() + "\n\n"
            except Exception as e:
                # missing or poorly formatted addon.xml
                print("Excluding %s for %s" % (addon_xml_path, e))
        
        # clean and add closing tag
        addons_xml = addons_xml.strip() + "\n</addons>\n"
        
        # save file
        self._save_file(addons_xml, file=os.path.join(self.config.repo_path, "addons.xml"))

    def _generate_repo_addons_md5_file(self):
        print("Generating addons.xml.md5 file")
        
        try:
            # create a new md5 hash
            m = hashlib.md5(open(os.path.join(self.config.repo_path, "addons.xml"), 'r').read().encode('utf-8')).hexdigest()
            
            # save file
            self._save_file(m, file=os.path.join(self.config.repo_path, "addons.xml.md5"))
        except Exception as e:
            # oops
            print("An error occurred creating addons.xml.md5 file!\n%s" % e)

    def _save_file(self, data, file):
        try:
            # write data to the file
            open(file, "w").write(data)
        except Exception as e:
            # oops
            print("An error occurred saving %s file!\n%s" % (file, e))


class Copier:
    def __init__(self, config):
        self.config = config
        self._copy_additional_files()

    def _copy_additional_files(self):
        #os.chdir(os.path.abspath(os.path.join(tools_path, os.pardir)))
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
                addon_out_path = os.path.join(self.config.out_dir, self.config.repo_path, addon_id)
                addon_out_path = os.path.join(addon_out_path, '')
                
                try:
                    # copy addon.xml
                    shutil.copy2(addon_xml_path, addon_out_path)
                    
                    # copy changelog.txt
                    changelog_txt_path = self._find_files("changelog*.txt", addon_folder)
                    for changelog in changelog_txt_path:
                        shutil.copy2(os.path.join(addon_folder, changelog), addon_out_path)
                    
                    # copy icon.png
                    icon_png_path = self._find_files("icon*.png", addon_folder)
                    for icon in icon_png_path:
                        shutil.copy2(os.path.join(addon_folder, icon), addon_out_path)
                    
                    # copy fanart.jpg
                    fanart_jpg_path = self._find_files("fanart*.jpg", addon_folder)
                    for fanart in fanart_jpg_path:
                        shutil.copy2(os.path.join(addon_folder, fanart), addon_out_path)
                except IOError:
                    pass
    
    def _find_files(self, which, where='.'):
        rule = re.compile(fnmatch.translate(which), re.IGNORECASE)
        return [name for name in os.listdir(where) if rule.match(name)]

class Config:
    def __init__(self):
        # create the cli argument parser
        parser = self._init_parser()
        
        # get the settings from the config file
        config = self._read_config_file(CONFIG_FILE)
        
        # merge config file and cli arguments
        args = parser.parse_args()
        argparse_dict = vars(args)
        config.update(argparse_dict)
        
        # check the config parameter
        self._validate_config(config)
        
        # add the config attributes to this instance
        for key, value in config.items():
            setattr(self, key, value)
        
        # the path of the addon repository
        self.repo_path = os.path.join(self.out_dir, self.addon_id)
        
        # save the config to file
        self._write_config_file(config, CONFIG_FILE)
    
    def _init_parser(self):
        parser = ArgumentParser(description="Create a Kodi repository")
        parser.add_argument('-n', '--name', metavar='Repository name', type=str, dest='repo_name', \
                            help="The name of the repository")
        parser.add_argument('-r', '--id', metavar='Repository addon ID', type=str, dest='addon_id', \
                            help="The ID of the repository addon (must start with 'repository.')")
        parser.add_argument('-v', '--version', metavar='Version', type=str, dest='version', \
                            help="The version of the repository addon")
        parser.add_argument('-a', '--author', metavar='Author', type=str, dest='author', \
                            help="The author of the repository")
        parser.add_argument('-s', '--summary', metavar='Summary', type=str, dest='summary', \
                            help="A short summary of this repository")
        parser.add_argument('-d', '--description', metavar='Description', type=str, dest='description', \
                            help="The description can be longer. Using [CR] you can create a newline. The use of other markup is not advised.")
        parser.add_argument('-u', '--url', metavar='Remote repository URL', type=str, dest='url', \
                            help="The later URL of the repository main directory, e.g. https://raw.githubusercontent.com/Your-Github-Username/repository-link/")
        parser.add_argument('-i', '--input-dir', metavar='Input directory', type=str, dest='in_dir', \
                            help="The directory containing the addons that should be added to the repository")
        parser.add_argument('-o', '--output-dir', metavar='Output directory', type=str, dest='out_dir', \
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
                    not parsed_url.netloc or \
                    not parsed_url.path:
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
            print('the following arguments are required:\n\t%s' %
                         '\n\t'.join(missing_args), file=sys.stderr)
            sys.exit(1)
        if wrong_args:
            print('there were errors with the following arguments:\n\t%s' %
                         '\n\t'.join(wrong_args), file=sys.stderr)
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
            except:
                config = {}
        
        # return the content of the config file as dict
        return config
    
    def _write_config_file(self, config, file_path):
        # write the config to file
        with open(file_path, 'w') as f:
                json.dump(config, f)



if __name__ == "__main__":
    # load the config
    config = Config()
    
    Generator(config)
    Copier(config)
    print("Finished updating addons xml & md5 files, zipping addons and copying additional files")
