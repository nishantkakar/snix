#!/usr/bin/env python
import urllib2
import os
import zipfile
import subprocess

import sys
from snixLogger import SnixLogger
from contextlib import contextmanager

logger = SnixLogger.logger()


def abort(msg):
    logger.error(" -Aborting!- %s" % msg)
    sys.exit(1)


def execute(cmd, use_shell):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=use_shell)
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        else:
            sys.stdout.write(output)
            sys.stdout.flush()

    return process.poll()


@contextmanager
def execute_in_dir_and_revert(target_dir):
    original_dir = os.getcwd()
    try:
        logger.info("Switching to directory...{0}".format(target_dir))
        os.chdir(target_dir)
        yield
    finally:
        logger.info("Reverting back to directory...{0}".format(original_dir))
        os.chdir(original_dir)



# TODO validate url and destination. Might be a good method to start unit testing
def downloadFile(url, targetDir):
    if not os.path.isdir(targetDir):
        raise ValueError("Will not download to a non existant directory:{}".format(targetDir))
    if not os.access(targetDir, os.W_OK):
        raise ValueError("Directory {} should be writable".format(targetDir))
    fileName = os.path.basename(url)
    file = os.path.join(targetDir, fileName)
    if not os.path.exists(file):
        res = urllib2.urlopen(url)
        with open(file, "wb") as f:
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
