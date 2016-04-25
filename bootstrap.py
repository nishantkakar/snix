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

SNIX_DIRNAME="snix"
SNIX_CODE_DIRNAME="__snix__"

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
	logger.info("Installing Xcode Developer Tools")
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
def gitcloneSnix(snixDir):
	"""Clones the Snix repository from Github."""
	try:
		subprocess.check_call(["git","clone","https://github.com/yaise/snix.git",snixDir],stdin=None,shell=False)
	except subprocess.CalledProcessError as e:
		abort("{0} exited with error code{1}".format(e.cmd,e.returncode))

def setupSnix(destinationDir):
	"""Ensures that Snix repository is setup."""
	logger.info("Setting up Snix in {0}".format(destinationDir))
	global DEVNULL
	global SNIX_DIRNAME
	global SNIX_CODE_DIRNAME
	if not os.path.isdir(destinationDir):
		abort("{0} is not a valid directory".format(destinationDir))
	snixDir = os.path.join(destinationDir,SNIX_DIRNAME)
	snixCodeDir = os.path.join(snixDir,SNIX_CODE_DIRNAME)
	if os.path.exists(snixDir):
		if os.path.exists(snixCodeDir)  and if os.path.exists(not os.path.exists(os.path.join(snixCodeDir,".git")):
		abort("{0} . Deleting {0} is recommended.".format(snixDir))
	else:
		logger.info("Setting up Snix")
		logger.info("Creating  {0}".format(snixDir)) 
		not found. Will clone from Github.".format(snixDir))
		gitcloneSnix(snixDir)
	return snixDir

def snixInit(snixDir):
	logger.info("Switching to Snix directory: {0}".format(snixDir))
	os.chdir(snixDir)
	subprocess.call(os.path.join(snixDir,"snix") + " init",shell=True)

def getBootstrapForThisOS():
	return {
		'Darwin':bootstrapMac
	}.get(platform.system())	

def bootstrapMac():
	xCodeCLI()

#TODO Need to differentiate between snix( the core project ) and the custom snix install for the client. Check if there's a way to package a snix project. otherwise dump everything in a /bin folder
# what should be the landing folder name : snix
# what should be the sub folder name where snix gets installed ; __snix__
# put the required binaries or soft links into snix/bin folder. put snix/bin on the path.  
# put a sample.manifest in a snix/
# put a README in snix/ Mention why this structure exists. if someone changes files, they should branch it out first or perhaps when I pull down snix I can create a local branch for edits
# put a .gitignore file that ignores __snix__ and the bin/ and the sample.manifest and the README file. 
def bootstrap():
	logger.info("Hi! there. Let's get started!")
	osBootstrap = getBootstrapForThisOS()
	osBootstrap()
	snixDir = setupSnix(HOME)
	logger.info("----->Bootstrap DONE. Handing over to Snix.<-----")
	snixInit(snixDir)

if __name__ == "__main__":
	bootstrap()
