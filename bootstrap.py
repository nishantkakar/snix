import argparse
import os
import platform
import re
import shlex
import subprocess
import time
import logging
import socket
import sys

HOME = os.environ['HOME']
DEFAULT_INSTALL_DIR_NAME = 'muley'
SNIX_CODE_DIRNAME = "__snix__"

DEVNULL = open(os.devnull, 'w')

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s-%(levelname)s-%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)


def abort(msg):
    logger.error(' -Aborting!- %s'% msg)
    sys.exit(1)


def network_up():
    """Checks if the network is up. Returns a tuple(True/False, message)"""
    # noinspection PyBroadException
    msg = 'Checking network...'
    try:
        host = socket.gethostbyname("www.google.com")
        socket.create_connection((host, 80), 2)
        return True, msg + 'UP!'
    except:
        pass
    return False, msg + 'DOWN!'


def precondition(pre):
    """A function decorator that will wrap the target function with a precondition.
    Preconditions themselves are functions that MUST return a tuple(True/False,Message)"""

    def decorate(func):
        def with_precondition(*args, **kwargs):
            (result, message) = pre()
            if result:
                logger.info(message)
                func(*args, **kwargs)
            else:
                abort(message)
            return result

        return with_precondition

    return decorate


# @precondition(network_up)
# def gitcloneSnix(snixDir):
#     """Clones the Snix repository from Github."""
#     try:
#         subprocess.check_call(["git", "clone", "https://github.com/yaise/snix.git", snixDir], stdin=None, shell=False)
#     except subprocess.CalledProcessError as e:
#         abort("{0} exited with error code{1}".format(e.cmd, e.returncode))

@precondition(network_up)
def _clone_repo_into(snix_root):
    msg='Snix repo...'
    if not os.path.exists(snix_root):
        abort('%s does not exist!' % msg)
    snix_repo = os.path.join(snix_root, SNIX_CODE_DIRNAME)
    snix_repo_git = os.path.join(snix_repo, '.git')
    if not os.path.exists(snix_repo):
        try:
            subprocess.check_call(["git", "clone", "https://github.com/yaise/snix.git", snix_repo], stdin=None, shell=False)
        except subprocess.CalledProcessError as e:
            abort("{0} exited with error code{1}".format(e.cmd, e.returncode))
    else:
        if os.path.exists(snix_repo_git):
            logger.info('found! Will update.')
            try:
                subprocess.check_call(["git", "--git-dir=%s"%snix_repo_git,"pull"], stdin=None, shell=False)
            except subprocess.CalledProcessError as e:
                abort("{0} exited with error code{1}".format(e.cmd, e.returncode))
            return
        else:
            logger.info(msg+'directory exists but no repository found. Deleting %s' % snix_repo)
            os.rmdir(snix_repo)

    logger.info(msg+'done!')


def setup_snix_in(snix_root):
    """Sets up the Tree structure for snix."""
    msg = 'Snix...'
    global SNIX_CODE_DIRNAME
    if not os.path.exists(snix_root):
        logger.info(msg + 'creating dir:' + snix_root)
        os.mkdir(snix_root)
    else:
        logger.info(msg + '%s already exists.' % snix_root)

    _clone_repo_into(snix_root)


    return snix_root


# def snixInit(snixDir):
#     logger.info("Switching to Snix directory: {0}".format(snixDir))
#     os.chdir(snixDir)
#     subprocess.call(os.path.join(snixDir, "snix") + " init", shell=True)


def _get_bootstrap_for_this_os():
    return {
        'Darwin': _bootstrap_darwin
    }.get(platform.system())


@precondition(network_up)
def _install_xcode_devtools():
    """" Installs Xcode developer tools without any UI intervention. Credit :
    https://github.com/timsutton/osx-vm-templates/blob/ce8df8a7468faa7c5312444ece1b977c1b2f77a4/scripts/xcode-cli-tools.sh """

    msg = 'XCode Developer Tools...'
    if os.path.exists(os.path.join(os.sep, 'Library', 'Developer', 'CommandLineTools')):
        logger.info(msg + "already installed!")
        return

    ver = re.match(r'(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)', platform.mac_ver()[0])
    if not int(ver.group('major')) >= 10 and not int(ver.group('minor')) >= 9:
        abort('Do not support OSX version lower than 10.9. Sorry.')

    tmp_file = '/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress'
    open(tmp_file, 'a').close()
    os.utime(tmp_file, None)

    try:
        logger.info(msg + 'searching')
        list_updates = subprocess.Popen(["softwareupdate", "-l"], stdout=subprocess.PIPE)
        find_xcode_cli = subprocess.Popen(["grep", "*.*Command Line"], stdin=list_updates.stdout,
                                          stdout=subprocess.PIPE)
        result = find_xcode_cli.communicate()[0]
        if result is None:
            abort(msg + " Not found.")
        tool_name = result.split('*')[1].strip()
        list_updates.stdout.close()

        logger.info(msg + 'installing ' + tool_name)
        install = subprocess.Popen(["softwareupdate", "-iv", tool_name], stdin=None, stdout=subprocess.PIPE)
        while True:
            output = install.stdout.readline()
            if output == '' and install.poll() is not None:
                break
            else:
                sys.stdout.write(output)
                sys.stdout.flush()
    except subprocess.CalledProcessError as e:
        abort(msg + '{0} exited with error code{1}'.format(e.cmd, e.returncode))

    logger.info(msg + 'done!')


@precondition(network_up)
def _install_homebrew():
    msg = 'Homebrew...'

    logger.info(msg + 'installing')
    try:
        cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        if out:
            logger.info(msg + out)
        if err:
            logger.info(msg + err)
    except subprocess.CalledProcessError as e:
        abort(msg + '{0} exited with error code{1}'.format(e.cmd, e.returncode))

    logger.info(msg + 'done!')


def _bootstrap_darwin():
    _install_xcode_devtools()
    _install_homebrew()


# TODO Need to differentiate between snix( the core project ) and the custom snix install for the client. Check if there's a way to package a snix project. otherwise dump everything in a /bin folder
# put the required binaries or soft links into snix/bin folder. put snix/bin on the path.
# put a sample.manifest in a snix/
# put a README in snix/ Mention why this structure exists. if someone changes files, they should branch it out first or perhaps when I pull down snix I can create a local branch for edits
# put a .gitignore file that ignores __snix__ and the bin/ and the sample.manifest and the README file.
def _bootstrap():
    os_bootstrap = _get_bootstrap_for_this_os()
    os_bootstrap()
    snix_dir = setup_snix_in(os.path.join(HOME, DEFAULT_INSTALL_DIR_NAME))
    logger.info("----->Bootstrap DONE. Changing Directory to %s.<-----" % snix_dir)
    # dump output
    # ask to proceed with installation ( y/n )
    # snixInit(snix_dir)


if __name__ == "__main__":
    logger.info("Hi! there. Let's get started!")
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--install_dir_name',
                        help='Name for the installation directory ($HOME/<install_dir_name>) '
                             'which will hold your code and configs')
    # parser.add_argument('-g', '--github_user', help='Your github username')
    # parser.add_argument('-e', '--email', help='Your email address')
    args = parser.parse_args()
    if not args.install_dir_name:
        args.install_dir_name = raw_input(
            'Please enter a directory name to create in $HOME[%s]:' % DEFAULT_INSTALL_DIR_NAME) or DEFAULT_INSTALL_DIR_NAME
    # if not args.github_user:
    #     args.github_user = raw_input('Please enter your github username:')
    # if not args.email:
    #     args.email = raw_input('Please enter your email address:')

    _bootstrap()


#TESTS:
##bootsrap from remote location.
##bootstrap the second time after running it for the first time - again from remote location.
    #xcode - ok
    #brew - ok
    #snix - repo - update if already exists.
##bootstrap third time after setting up from within the repo.
  # ask for location.
  # if it's there and the repo is there, then udpate the repo.