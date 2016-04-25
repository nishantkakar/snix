#!/usr/bin/env python

import ConfigParser
import os
import snixItem
import snixCore

MANIFEST = os.path.join(os.environ['PWD'],"manifest.ini")

class Manifest:
	"""Reprents the parsed version of the manifet that contains snix coniguration."""
	__metaclass__ = snixCore.Singleton

	@staticmethod
	def parse(file=MANIFEST):
		manifest = Manifest(file)
		manifest._parseManifest()
		return manifest
		
	def __init__(self, file=MANIFEST):
		if not os.path.isfile(file):
			raise ValueError("%s is not a valid file path."%file)
		self.parser = ConfigParser.SafeConfigParser(os.environ)
		self.file = file

	def _parseManifest(self):
		self.parser.read(self.file)
		self.config = dict(self.parser.items("configuration"))
	
	# make this take in a filter. 
	def getItems(self):
		rint(self.parser.items("items"))
		return list(map(self.getItem,self.parser.items("items")))
		#return self.parser.items("items")

	def getConfigurationValue(self, key):
		return self.config[key.lower()]
	
	def getItem(self, key):	
		if not self.parser.has_option("items",key):
			return snixItem.MissingItem(key)
		else:
			# TODO : what if value is between "" and not ''
			self.config[key] = self.parser.get("items", key).strip('\'')
			return snixItem.Item(key, self.config)

if __name__ == "__main__":
	manifest = Manifest.parse()
	print(manifest.getItems())
