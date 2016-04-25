#!/usr/bin/env python
import urllib2
import os
import zipfile
import subprocess

NOTE: Do not use the logger here as it will result in a cyclic import 'cos of the Singleton. Maybe it needs to be it's own little thing. 
class Singleton(type):
        instance = None
        def __call__(cls, *args, **kwargs):
                if cls.instance is None:
                        cls.instance = super(Singleton,cls).__call__(*args,**kwargs)
                return cls.instance

def executeCommand(cmd, executeInShell):
	process = subprocess.Popen(cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell = executeInShell)
        return process.communicate()

#TODO validate url and destination. Might be a good method to start unit testing
def downloadFile(url, targetDir):
	if not os.path.isdir(targetDir):
		raise ValueError("Will not download to a non existant directory:{}".format(targetDir))
	if not os.access(targetDir, os.W_OK):
		raise ValueError("Directory {} should be writable".format(targetDir))
	fileName = os.path.basename(url)
	file = os.path.join(targetDir,fileName)
	if not os.path.exists(file):
		res = urllib2.urlopen(url)
		with open(file , "wb") as f:
			f.write(res.read())
		f.close()
	return file		

def extractIfCompressed(filePath, subDir):
	if not os.path.exists(filePath):
		raise ValueError("Cannot extract a non-existant file:{}".format(filePath))
	extractedLocation = os.path.join(os.path.dirname(filePath), subDir)
	if zipfile.is_zipfile(filePath):
		zf = zipfile.ZipFile(filePath)
		zf.extractall(extractedLocation)
		zf.close()
	else:
		raise ValueError("{} is not a valid compressed file.".format(filePath))
	return extractedLocation
