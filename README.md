# [Kodi](https://kodi.tv/) Repository Bootstrapper
Many thanks to [@Twilight0](https://github.com/Twilight0) and all the others who contributed code for this project before.


## Installation
You can install this Python package via pip(x):

```shell
pip(x) install kodi-repo-bootstrap
```

Otherwise the package can be downloaded from PyPI: https://pypi.org/project/kodi-repo-bootstrap/



## Usage
### 1. Preperations
You need two directories:

- `addons_dir`: This direcotry contains the Kodi addons you want to publish. The single addons can be present as ZIP files or as a directory with the official [Kodi addon structure](https://kodi.wiki/view/Add-on_structure).

    A valid `addons_dir` will look like this:
    ```
    addons_dir/
        |- plugin.addon.id-versionX.zip
        - and / or -
        |- plugin.addon.id/
        |    |- addon.xml
        |    |- ...
        |    - and / or -
        |    |- plugin.addon.id-versionX.zip
    ```
    If multiple versions of the same addon (same ID) are present, only the newest version will be used by the script.

- `repo_dir` where this script creates the necessary structure for a Kodi repository. **Please do not make any manual changes to this directory.**


### 2. Define repository settings
Create a configuration file in JSON format (e.g. `config.json`). An example file with the available options can be found in the root directory of this repository: [config.json.example](https://github.com/mammo0/kodi-repo-bootstrap/blob/master/config.json.example)

**OR**

Configure the Kodi repository with CLI arguments. See
```shell
kodi-repo-bootstrap -h
```
for the available settings.


### 3. Run the script
```shell
kodi-repo-bootstrap <CONFIG_FILE>
```
**The path to the config file is mandatory.**

This will create all files and directories that are necessary for a Kodi repository. No user interaction is needed.


### 4. Publish the `repo_dir` e.g. via HTTP server (webdav)
The `repo_dir` contains all files and directories that are necessary for Kodi to recognize it as a valid repository. You only have to publish it via HTTP.

For a simple Webdav setup with Docker, you can have a look at my other repository: [docker-webdav](https://github.com/mammo0/docker-webdav)


### 5. *[Optional]* Change repository settings
To change any settings you can either

- adjust the config file

**OR**

- use a CLI argument. The script will then save the changes to the config file for you.



## Troubleshooting
If you encounter any errors, please clear the `repo_dir` first and run the script again. This will recreate the Kodi repository file structure.

If the error is still present, feel free to open an issue on GitHub.
