#!/usr/bin/env python
import re
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
        def __init__(self, name, config):
                self.name,self.config = name, config
                self.installer = Installer.forItem(name, config)

        def install(self):
		logger.info("Installing Item : {0}".format(self.name))	
                self.installer.install()

        def remove(self):
		logger.info("Removing Item : {0}".format(self.name))	
                self.installer.remove()

        def update(self):
		logger.info("Updating Item : {0}".format(self.name))	
                self.installer.update()

class MissingItem(Item):
	"""Represents a missing item that will not be installed. """
	def __init__(self, key):
		self.key = key
	def install(self):
		logger.warn("Will not install missing item:{0}!".format(self.key))

	def remove(self):
		logger.warn("Will not remove missing item:{0}!".format(self.key))

	def update(self):
		logger.warn("Will not update missing item:{0}!".format(self.key))

#TODO : Should installer hold the cmdData. How do I ensure that it's private and cannot be modified?
class Installer:
	"""The Snix Installer. The factory method will interpret the value for the item name and create an appropriate installer."""

	@staticmethod
        def forItem(name, config):
		BREW_PATTERN = re.compile(r"^[bB]rew(-[cC]ask)?$",re.I)
		INET_PATTERN = re.compile(r"^http[s]?:\/\/")
		LOCAL_PATTERN = re.compile(r"^file:\/\/")
		value = config[name]
		parsedUrl = urlparse.urlparse(value)
		if re.match(BREW_PATTERN, value):
			return BrewInstaller(name, config)
		elif parsedUrl.scheme and parsedUrl.netloc:
			return UrlInstaller(name, config)
		else:
			return CommandInstaller(name, config)

	def __init__(self,name, config):
		self.name = name
		self.config = config
		if not config[name]:
			raise ValueError("{0} must be in passed in configuration".format(self.name))

	def getInstallCmd(self): 
		"""Override this to pass back an install command and whether it should be executed in a shell. It is the installer's responsibility to make sure that the command isn't harmful, especially if it expects the to be run in a shell."""
		pass	

        def install(self): 
		cmd, executeInShell = self.getInstallCmd()
		logger.info("Executing command:{} via {}".format(cmd, self.getInstallerType()))
		stdout_data,stderr_data = snixCore.executeCommand(cmd, executeInShell)
		if stdout_data:
			logger.debug(stdout_data)
		if stderr_data:
			logger.debug(stderr_data)

	def getInstallerType(self):
		pass

class CommandInstaller(Installer):
	"""An Installer that will execute a command."""
	#TODO : parse the command and make sure it's not dangerous
	def __init__(self, name, config):
		Installer.__init__(self, name, config)
		self.cmdData = config[name]

	def getInstallerType(self):
		return "Command Line"

	def getInstallCmd(self):
		"""No need to change the command."""
		return self.cmdData, True

class BrewInstaller(Installer):
	"""An Installer that will brew an item."""
	def __init__(self, name, config):
		Installer.__init__(self, name, config)
		self.cmdData = name
	
	def getInstallerType(self):
		return "HomeBrew"

	def getInstallCmd(self):
		if re.match(r"^[bB]rew$",self.config[self.name]): 
			cmd = ["brew","install",self.cmdData]
		else:
			cmd = ["brew","cask", "install", self.cmdData]
		return cmd, False
	
class UrlInstaller(Installer):
	"""An Installer that will download and install a package from a given URL."""
	def __init__(self, name, config):
		Installer.__init__(self, name, config)
		self.url = config[name]

	def getInstallerType(self):
		return "Downloaded File"

	def install(self):
		logger.info("Downloading {} from url:{}".format(self.name, self.url)) 
		file = snixCore.downloadFile(self.url,self.config["workingdir"])	
		logger.info("Extracting {}".format(file))
		file = snixCore.extractIfCompressed(file, self.name)
		logger.info("Extracted location:{}".format(file))
		app = glob.glob(os.path.join(file,"*.app"))[0]
		if app:
			logger.info("Copying {} to /Applications".format(app))
			shutil.copytree(app, os.path.join("/Applications",os.path.basename(app)))		
		#if compressed file uncompress
		#if dmg then attach the dmg to /tmp/name/name-dmg
		#if /tmp/name-dmg/ is an app, then copy to applications
		#detach the dmg
		#if /tmp/name-dmg is a pkg. then we need to install with escalated privileges and wait for it to complete. 
	
if __name__ == "__main__":
	Item("test","ruby -e \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\"").install()
	Item("testBrew","brew").install()
