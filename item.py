#!/usr/bin/env python
import re
import shlex
import urlparse
import subprocess
import snixLogger
import urllib2
import snixCore
import shutil
import os
import glob

logger = snixLogger.SnixLogger.logger()


class Item:
    """Represents a basic item that needs to be managed by Snix. Support install, remove and update of an item."""

    def __init__(self, context):
        if not type(context) is dict:
            snixCore.abort('Cannot install an item without the configuration.')

        self._context = context
        # ?self._installer = CommandBuilder.build_install_cmd(item, context)

    def install(self):
        msg = "Installing {0}...".format(self._context['name'])
        cmd, use_shell = CommandBuilder.build_install_cmd(self._context)
        logger.info(msg+cmd)
        ret = snixCore.execute(shlex.split(cmd), use_shell)
        #logger.info(msg+'StatusCode:'+str(ret))
        logger.info(msg+'Done!. StatusCode:'+str(ret))
        # if out:
        #     logger.debug(out)
        # if err:
        #     logger.error(err)

    # def remove(self):
    #     logger.info("Removing Item : {0}".format(self._item))
    #     self._installer.remove()
    #
    # def update(self):
    #     logger.info("Updating Item : {0}".format(self._item))
    #     self._installer.update()


class CommandBuilder(object):

    @staticmethod
    def build_install_cmd(context):
        brew_pattern = re.compile(r"^[bB]rew(-[cC]ask)?$", re.I)
        # INET_PATTERN = re.compile(r"^http[s]?:\/\/")
        # LOCAL_PATTERN = re.compile(r"^file:\/\/")
        via = context['via']
        # parsedUrl = urlparse.urlparse(via)
        if re.match(brew_pattern, via):
            if re.match(r"^[bB]rew$", via):
                # cmd = ["brew", "install", item['name']]
                cmd = "brew install {0}".format(context['name'])
            else:
                # cmd = ["brew", "cask", "install", item['name']]
                cmd = "brew cask install {0}".format(context['name'])
            return cmd, False
#
#
# # TODO fix my parameters
# class MissingItem(Item):
#     """Represents a missing item that will not be installed. """
#
#     def __init__(self, key):
#         self.key = key
#
#     def install(self):
#         logger.warn("Will not install missing item:{0}!".format(self.key))
#
#     def remove(self):
#         logger.warn("Will not remove missing item:{0}!".format(self.key))
#
#     def update(self):
#         logger.warn("Will not update missing item:{0}!".format(self.key))
#
#
# # TODO : Should installer hold the cmdData. How do I ensure that it's private and cannot be modified?
# class Installer:
#     """The Snix Installer. The factory method will interpret the value for the item name and create an appropriate installer."""
#
#     @staticmethod
#     def for_item(item, context):
#         brew_pattern = re.compile(r"^[bB]rew(-[cC]ask)?$", re.I)
#         # INET_PATTERN = re.compile(r"^http[s]?:\/\/")
#         # LOCAL_PATTERN = re.compile(r"^file:\/\/")
#         via = item['via']
#         # parsedUrl = urlparse.urlparse(via)
#         if re.match(brew_pattern, via):
#             return BrewInstaller(item, context)
#         # elif parsedUrl.scheme and parsedUrl.netloc:
#         #     return UrlInstaller(item, context)
#         # else:
#         #     return CommandInstaller(item, context)
#
#     def __init__(self, name, config):
#         self.name = name
#         self.config = config
#
#     def get_install_cmd(self):
#         """Override this to pass back an install command and whether it should be executed in a shell. It is the installer's responsibility to make sure that the command isn't harmful, especially if it expects the to be run in a shell."""
#         pass
#
#     def install(self, name):
#         cmd, executeInShell = self.get_install_cmd(name)
#         logger.info("Executing command:{} via {}".format(cmd, self.get_type()))
#         stdout_data, stderr_data = snixCore.execute(cmd, executeInShell)
#         if stdout_data:
#             logger.debug(stdout_data)
#         if stderr_data:
#             logger.error(stderr_data)
#
#     def get_type(self):
#         pass
#
#
# class CommandInstaller(Installer):
#     """An Installer that will execute a command."""
#
#     # TODO : parse the command and make sure it's not dangerous
#     def __init__(self, name, config):
#         Installer.__init__(self, name, config)
#         self.cmdData = config[name]
#
#     def get_type(self):
#         return "Command Line"
#
#     def get_install_cmd(self):
#         """No need to change the command."""
#         return self.cmdData, True
#
#
# class BrewInstaller(Installer):
#     """An Installer that will brew an item."""
#
#     def __init__(self, name, config):
#         Installer.__init__(self, name, config)
#         self.cmdData = name
#
#     def get_type(self):
#         return "HomeBrew"
#
#     def get_install_cmd(self):
#         if re.match(r"^[bB]rew$", self.config[self.name]):
#             cmd = ["brew", "install", self.cmdData]
#         else:
#             cmd = ["brew", "cask", "install", self.cmdData]
#         return cmd, False
#
#
# class UrlInstaller(Installer):
#     """An Installer that will download and install a package from a given URL."""
#
#     def __init__(self, name, config):
#         Installer.__init__(self, name, config)
#         self.url = config[name]
#
#     def get_type(self):
#         return "Downloaded File"
#
#     def install(self):
#         logger.info("Downloading {} from url:{}".format(self.name, self.url))
#         file = snixCore.downloadFile(self.url, self.config["workingdir"])
#         logger.info("Extracting {}".format(file))
#         file = snixCore.extractIfCompressed(file, self.name)
#         logger.info("Extracted location:{}".format(file))
#         app = glob.glob(os.path.join(file, "*.app"))[0]
#         if app:
#             logger.info("Copying {} to /Applications".format(app))
#             shutil.copytree(app, os.path.join("/Applications", os.path.basename(app)))
#         # if compressed file uncompress
#         # if dmg then attach the dmg to /tmp/name/name-dmg
#         # if /tmp/name-dmg/ is an app, then copy to applications
#         # detach the dmg
#         # if /tmp/name-dmg is a pkg. then we need to install with escalated privileges and wait for it to complete.
#
#
# if __name__ == "__main__":
#     Item("test",
#          "ruby -e \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\"").install()
#     Item("testBrew", "brew").install()
