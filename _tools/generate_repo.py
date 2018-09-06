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
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
from urllib.parse import urlparse
from xml.dom import minidom
import zipfile


# global variables
CONFIG_FILE = 'config.json'

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

        # travel path one up
        os.chdir(os.path.abspath(os.path.join(tools_path, os.pardir)))

        # generate files
        self._pre_run()
        self._generate_repo_files()
        self._generate_addons_file()
        self._generate_md5_file()
        self._generate_zip_files()

    def _pre_run(self):

        # create output  path if it does not exists
        if not os.path.exists(self.config.out_dir):
            os.makedirs(self.config.out_dir)

    def _generate_repo_files(self):

        if os.path.isfile(self.config.addon_id + os.path.sep + "addon.xml"):
            return

        print("Create repository addon")

        with open(tools_path + os.path.sep + "template.xml", "r") as template:
            template_xml = template.read()

        repo_xml = template_xml.format(
            addonid=self.config.addon_id,
            name=self.config.repo_name,
            version=self.config.version,
            author=self.config.author,
            summary=self.config.summary,
            description=self.config.description,
            url=self.config.url,
            output_path=self.config.out_dir)

        # save file
        if not os.path.exists(self.config.addon_id):
            os.makedirs(self.config.addon_id)

        self._save_file(repo_xml.encode("utf-8"), file=self.config.addon_id + os.path.sep + "addon.xml")

    def _generate_zip_files(self):
        addons = os.listdir(".")
        # loop thru and add each addons addon.xml file
        for addon in addons:
            # create path
            _path = os.path.join(addon, "addon.xml")
            # skip path if it has no addon.xml
            if not os.path.isfile(_path):
                continue
            try:
                # skip any file or .git folder
                if not (os.path.isdir(addon) or addon == ".idea" or addon == ".git" or addon == ".svn" or addon == self.config.out_dir or addon == tools_path):
                    continue
                # create path
                _path = os.path.join(addon, "addon.xml")
                # split lines for stripping
                document = minidom.parse(_path)
                for parent in document.getElementsByTagName("addon"):
                    version = parent.getAttribute("version")
                    addonid = parent.getAttribute("id")
                self._generate_zip_file(addon, version, addonid)
            except Exception as e:
                print(e)

    def _generate_zip_file(self, path, version, addonid):
        print("Generate zip file for " + addonid + " " + version)
        filename = path + "-" + version + ".zip"
        try:
            zip = zipfile.ZipFile(filename, 'w', compression=zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(path + os.path.sep):
                if '.idea' in dirs:
                    dirs.remove('.idea')
                if '.git' in dirs:
                    dirs.remove('.git')
                zip.write(os.path.join(root))
                for file in files:
                    zip.write(os.path.join(root, file))

            zip.close()

            if not os.path.exists(self.config.out_dir + addonid):
                os.makedirs(self.config.out_dir + addonid)

            if os.path.isfile(self.config.out_dir + addonid + os.path.sep + filename):
                # pass #uncomment to overwrite existing zip file, then comment or remove the next two lines below
                os.rename(self.config.out_dir + addonid + os.path.sep + filename,
                    self.config.out_dir + addonid + os.path.sep + filename + "." + datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
            shutil.move(filename, self.config.out_dir + addonid + os.path.sep + filename)
        except Exception as e:
            print(e)

    def _generate_addons_file(self):
        print("Generating addons.xml file")
        # addon list
        addons = os.listdir(".")
        # final addons text
        addons_xml = u"<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<addons>\n"
        # loop thru and add each addons addon.xml file
        for addon in addons:
            # create path
            _path = os.path.join(addon, "addon.xml")
            # skip path if it has no addon.xml
            if not os.path.isfile(_path):
                continue
            try:
                # split lines for stripping
                xml_lines = open(_path, "r").read().splitlines()
                # new addon
                addon_xml = ""
                # loop thru cleaning each line
                for line in xml_lines:
                    # skip encoding format line
                    if (line.find("<?xml") >= 0):
                        continue
                    # add line
                    addon_xml += line.rstrip() + "\n", "utf-8"
                # we succeeded so add to our final addons.xml text
                addons_xml += addon_xml.rstrip() + "\n\n"
            except Exception as e:
                # missing or poorly formatted addon.xml
                print("Excluding %s for %s" % (_path, e))
        # clean and add closing tag
        addons_xml = addons_xml.strip() + u"\n</addons>\n"
        # save file
        self._save_file(addons_xml.encode("utf-8"), file=self.config.out_dir + "addons.xml")

    def _generate_md5_file(self):
        print("Generating addons.xml.md5 file")
        try:
            # create a new md5 hash
            m = hashlib.md5(open(self.config.out_dir + "addons.xml").read()).hexdigest()
            # save file
            self._save_file(m, file=self.config.out_dir + "addons.xml.md5")
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
        os.chdir(os.path.abspath(os.path.join(tools_path, os.pardir)))
        addons = os.listdir(".")
        for addon in addons:
            xml_file = os.path.join(addon, "addon.xml")
            if not os.path.isfile(xml_file):
                continue
            if not (os.path.isdir(addon) or addon == ".idea" or addon == ".git" or addon == ".svn" or addon == self.config.out_dir or addon == tools_path):
                continue
            document = minidom.parse(xml_file)
            for parent in document.getElementsByTagName("addon"):
                version = parent.getAttribute("version")
                try:
                    if os.path.isfile(self.config.out_dir + addon + os.path.sep + "changelog-" + version + ".txt"):
                        pass
                    else:
                        shutil.copy(addon + os.path.sep + "changelog.txt", self.config.out_dir + addon + os.path.sep + "changelog-" + version + ".txt")
                except IOError:
                    pass
                try:
                    if os.path.isfile(self.config.out_dir + addon + os.path.sep + "icon.png"):
                        pass
                    else:
                        shutil.copy(addon + os.path.sep + "icon.png", self.config.out_dir + addon + os.path.sep + "icon.png")
                except IOError:
                    pass
                try:
                    if os.path.isfile(self.config.out_dir + addon + os.path.sep + "fanart.jpg"):
                        pass
                    else:
                        shutil.copy(addon + os.path.sep + "fanart.jpg", self.config.out_dir + addon + os.path.sep + "fanart.jpg")
                except IOError:
                    pass

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
            config['in_dir'] = Path(config['in_dir'])
            if not config['in_dir'].is_dir():
                wrong_args.append("--input-dir: a valid directory must be provided")
        if not config['out_dir']:
            missing_args.append("--output-dir")
        else:
            config['out_dir'] = Path(config['out_dir'])
            if not config['out_dir'].is_dir():
                wrong_args.append("--output-dir: a valid directory must be provided")
        
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
