#!/usr/bin/env python

import ConfigParser
import os
import snixItem

MANIFEST = os.path.join(os.environ['PWD'],"manifest")

#TODO : A static factory like method that would initialize the Manifest and parse it before returning an object
class Manifest:
	def __init__(self, manifest=MANIFEST):
		if not os.path.isfile(manifest):
			raise ValueError("%s is not a valid file path."%manifest)
		self.manifest = manifest
		self.config = ConfigParser.SafeConfigParser(os.environ)

	def parseManifest(self):
		self.config.read(self.manifest)
	
	# make this take in a filter. 
	def getItems(self):
		return self.config.items("items")

	def getConfigurationValue(self, key):
		return self.config.get("configuration",key)

	def getItem(self, key):
		#TODO : what if the key is invalid.
		return snixItem.Item(key,snixItem.Installer.forItem(self.config.get("items",key).strip('\'')))

if __name__ == "__main__":
	manifest = Manifest()
	manifest.parseManifest()
	print(manifest.getItems())
