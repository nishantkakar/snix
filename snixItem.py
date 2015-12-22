#!/usr/bin/env python
import re
import urlparse
import subprocess
import snixLogger

logger = snixLogger.SnixLogger.logger()

class Item:
	"""Represents a basic item that needs to be managed by Snix. Support install, remove and update of an item."""
        def __init__(self, name, installer):
                self.name = name
                self.installer = installer

        def install(self):
		logger.info("Installing {0}".format(self.name))	
                self.installer.install()

        def remove(self):
		logger.info("Removing {0}".format(self.name))	
                self.installer.remove()

        def update(self):
		logger.info("Updating {0}".format(self.name))	
                self.installer.update()

class Installer:
	"""The Snix Installer. Will interpret the key,value pair in the items section of the manifest and create the appropriate installers. """
	@staticmethod
        def forItem(value):
		BREW_PATTERN = re.compile(r"^brew$",re.I)
		INET_PATTERN = re.compile(r"^http[s]?:\/\/")
		LOCAL_PATTERN = re.compile(r"^file:\/\/")
		parsedUrl = urlparse.urlparse(value)
		if re.match(BREW_PATTERN,value):
			pass
		elif parsedUrl.scheme and parsedUrl.netloc:
			#return UrlInstaller(value)
			pass
		else:
			return CommandInstaller(value)
			
        def install(self): pass
        def remove(self): pass
        def update(self): pass

class CommandInstaller(Installer):
	"""An Installer that will execute a command. """
	def __init__(self, this):
		self.this = this

	def install(self):
		try:
			subprocess.call(self.this,shell=True)
		except subprocess.CalledProcessError as e:
			print("{0} exited with error code:{1}".format(e.cmd,e.returncode))

	
if __name__ == "__main__":
	Item("test",Installer.forItem("ruby -e \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)\"")).install()
	#Item("test",Installer.from("woo")).install()
