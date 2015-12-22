#!/usr/bin/env python
import os
import platform
import subprocess
import time
import logging
import socket
import sys

HOME = os.environ['HOME']
DEVNULL = open(os.devnull, 'w')

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s-%(levelname)s-%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)

def abort(message):
	logger.error(message+" -Aborting!-")
	sys.exit(1)

def networkUp():
	"""Checks if the network is up. Returns a tuple(True/False, message)"""
	try:
		host = socket.gethostbyname("www.google.com")
		socket.create_connection((host, 80), 2)
		return (True,"Checking Network: UP!")
	except:
		pass
	return (False,"Checking Network: DOWN!")

	
def precondition(pre):
	"""A function decorator that will wrap the target function with a precondition. Preconditions themeselves are functions that MUST return a tuple(True/False,Message)"""
	def decorate(func):
		def withPrecondition(*args,**kwargs):
			(result, message) = pre()
			if result:
				logger.info(message)
				func(*args,**kwargs)
			else:
				abort(message)
			return result
		return withPrecondition
	return decorate

@precondition(networkUp)
def installXCodeCLI():
	"""Spawns the Xcode Developer CLI tools installer."""
	logger.info("Installing XCode CLI tools.")
	subprocess.check_call(["xcode-select","--install"])
	
def xCodeCLI():
	"""Ensures that Xcode Developer Tools gets installed."""
	logger.info("Xcode Developer Tools")
	global DEVNULL
	waitForInstall = False
	for i in range(1,5):
		try:
			output = subprocess.check_output(["xcode-select","-p"],stdin=None, stderr=DEVNULL, shell=False)			
			logger.info(output)
			break
		except subprocess.CalledProcessError as e:
			if waitForInstall:
				secs = i*5
				logger.info("Waiting {0} more seconds for XCodeCLI to finish.".format(secs))
				time.sleep(secs)
			elif e.returncode == 2:
				result = installXCodeCLI()
				if not result:
					break
				waitForInstall = True

@precondition(networkUp)
def gitcloneSNIX(snixDir):
	"""Clones the SNIX repository from Github."""
	try:
		subprocess.check_call(["git","clone","https://github.com/yaise/snix.git",snixDir],stdin=None,shell=False)
	except subprocess.CalledProcessError as e:
		abort("{0} exited with error code{1}".format(e.cmd,e.returncode))

def setupSNIX(destinationDir):
	"""Ensures that SNIX repository is setup."""
	logger.info("SNIX in {0}".format(destinationDir))
	global DEVNULL
	if not os.path.isdir(destinationDir):
		abort("{0} is not a valid directory".format(destinationDir))
	snixDir = os.path.join(destinationDir,"snix")
	if os.path.exists(snixDir) and not os.path.exists(os.path.join(snixDir,".git")):
		abort("{0} doesn't seem to have a valid git repository. Deleting {0} is recommended.".format(snixDir))
	if not os.path.exists(snixDir):
		logger.info("{0} repository not found. Will clone from Github.".format(snixDir))
		gitcloneSNIX(snixDir)
	logger.info("Switching to SNIX directory: {0}".format(snixDir))
	os.chdir(snixDir)
	subprocess.call(os.path.join(snixDir,"snix") + " init",shell=True)

def getBootstrapForThisOS():
	return {
		'Darwin':bootstrapMac
	}.get(platform.system())	

def bootstrapMac():
	xCodeCLI()
		
def bootstrap():
	osBootstrap = getBootstrapForThisOS()
	osBootstrap()
	setupSNIX(HOME)

if __name__ == "__main__":
	bootstrap()
