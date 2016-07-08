import argparse
import json
import os
import platform
import re
import shlex
import subprocess
import logging
import socket
import sys

KEY_EMAIL = 'email'

KEY_GITHUB_USER = 'github_user'

SYS_HOME = os.environ['HOME']
SYS_PATH = os.environ['PATH']
SYS_USER = os.environ['USER']

DEFAULT_INSTALL_DIR_NAME = 'lab'
SNIX_CODE_DIR_NAME = '_snix'
SNIX_GROUP_MANIFEST_DIR_NAME = '_grp_manifest'
SNIX_USER_MANIFEST_DIR_NAME = '_user_manifest'
SNIX_RC_DIR_NAME = 'rc'

MY_SNIX_FILE_NAME = 'my.snix'

KEY_SNIX_MY_MANIFEST_DIR = 'snix_my_manifest_dir'
KEY_SNIX_USER_MANIFEST_DIR = 'snix_user_manifest_dir'
KEY_SNIX_GROUP_MANIFEST_DIR = 'snix_group_manifest_dir'
KEY_SNIX_RC_DIR = 'snix_rc_dir'
KEY_SNIX_ROOT = 'snix_root'

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s-%(levelname)s-%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.DEBUG)


def abort(msg):
    logger.error(" -Aborting!- %s" % msg)
    sys.exit(1)


def network_up():
    """Checks if the network is up. Returns a tuple(True/False, message)"""
    # noinspection PyBroadException
    msg = "Network..."
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
                return func(*args, **kwargs)
            else:
                abort(message)

        return with_precondition

    return decorate


@precondition(network_up)
def _clone_repo_into(msg, snix_root):
    """Clones the snix source code git repo"""
    if not os.path.exists(snix_root):
        abort("%s does not exist!" % msg)

    snix_repo = os.path.join(snix_root, SNIX_CODE_DIR_NAME)
    snix_repo_git = os.path.join(snix_repo, '.git')

    if not os.path.exists(snix_repo):
        try:
            subprocess.check_call(['git', 'clone', "https://github.com/yaise/snix.git", snix_repo], stdin=None,
                                  shell=False)
        except subprocess.CalledProcessError as e:
            abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
    else:
        if os.path.exists(snix_repo_git):
            logger.info(msg + "Found %s! Will update." % snix_repo)
            try:
                subprocess.check_call(['git', "--git-dir=%s" % snix_repo_git, "--work-tree=%s" % snix_repo, 'pull'],
                                      stdin=None, shell=False)
            except subprocess.CalledProcessError as e:
                abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
            return
        else:
            logger.info(msg + "Directory exists but no repository found. Deleting %s" % snix_repo)
            os.rmdir(snix_repo)

    logger.info(msg + 'Done!')


@precondition(network_up)
def setup_snix_in(snix_root):
    """Sets up the directory structure for snix."""
    msg = "Snix setup..."
    _config = {}
    _create_dir(msg, snix_root)
    _clone_repo_into(msg + "Cloning snix source code repo.", snix_root)
    _config[KEY_SNIX_ROOT] = snix_root

    snix_rc_dir = os.path.join(snix_root, SNIX_RC_DIR_NAME)
    _create_dir(msg + "Creating a location to store custom commands that can be sourced into the cli.", snix_rc_dir)
    _config[KEY_SNIX_RC_DIR] = snix_rc_dir

    group_manifest_dir = os.path.join(snix_root, SNIX_GROUP_MANIFEST_DIR_NAME)
    _create_dir(msg + "Creating a location to store manifests from teams/groups.", group_manifest_dir)
    _config[KEY_SNIX_GROUP_MANIFEST_DIR] = group_manifest_dir

    user_manifest_dir = os.path.join(snix_root, SNIX_USER_MANIFEST_DIR_NAME)
    _create_dir(msg + "Creating a location to store your and perhaps other user's manifests.", user_manifest_dir)
    _config[KEY_SNIX_USER_MANIFEST_DIR] = user_manifest_dir

    # TODO fix me: This obviously doesn't work. need the PATH modification to persist.
    logger.info(msg + "Adding %s to PATH" % snix_root)
    global SYS_PATH
    SYS_PATH += os.pathsep + snix_root
    logger.info(msg + "Path is:%s" % SYS_PATH)
    logger.info(msg + 'Done!')

    #TODO : Add a soft link to snix binary.

    return _config


def _create_dir(msg, snix_root):
    if not os.path.exists(snix_root):
        logger.info(msg + "Creating dir:" + snix_root)
        os.mkdir(snix_root)
    else:
        logger.info(msg + "%s already exists." % snix_root)


def _get_bootstrap_for_this_os():
    return {
        'Darwin': _bootstrap_darwin
    }.get(platform.system())


@precondition(network_up)
def _install_xcode_devtools():
    """" Installs Xcode developer tools without any UI intervention. Credit :
    https://github.com/timsutton/osx-vm-templates/blob/ce8df8a7468faa7c5312444ece1b977c1b2f77a4/scripts/xcode-cli-tools.sh """

    msg = "XCode Developer Tools..."
    if os.path.exists(os.path.join(os.sep, 'Library', 'Developer', 'CommandLineTools')):
        logger.info(msg + "Already installed!")
        return

    ver = re.match(r'(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)', platform.mac_ver()[0])
    if not int(ver.group('major')) >= 10 and not int(ver.group('minor')) >= 9:
        abort("Do not support OSX version lower than 10.9. Sorry.")

    tmp_file = "/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"
    open(tmp_file, 'a').close()
    os.utime(tmp_file, None)

    try:
        logger.info(msg + 'Searching')
        list_updates = subprocess.Popen(['softwareupdate', '-l'], stdout=subprocess.PIPE)
        find_xcode_cli = subprocess.Popen(['grep', "*.*Command Line"], stdin=list_updates.stdout,
                                          stdout=subprocess.PIPE)
        result = find_xcode_cli.communicate()[0]
        if result is None:
            abort(msg + "Not found.")
        tool_name = result.split('*')[1].strip()
        list_updates.stdout.close()

        logger.info(msg + 'Installing ' + tool_name)
        install = subprocess.Popen(['softwareupdate', '-iv', tool_name], stdin=None, stdout=subprocess.PIPE)
        while True:
            output = install.stdout.readline()
            if output == '' and install.poll() is not None:
                break
            else:
                sys.stdout.write(output)
                sys.stdout.flush()
    except subprocess.CalledProcessError as e:
        abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))

    logger.info(msg + 'Done!')


@precondition(network_up)
def _install_homebrew():
    msg = "Homebrew..."

    logger.info(msg + 'Installing')
    try:
        cmd = 'ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"'
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        out, err = process.communicate()
        if out:
            logger.info(msg + out)
        if err:
            logger.info(msg + err)

        process = subprocess.Popen(shlex.split("brew tap caskroom/cask"), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = process.communicate()
        if out:
            logger.info(msg + out)
        if err:
            logger.info(msg + err)

    except subprocess.CalledProcessError as e:
        abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))

    logger.info(msg + 'Done!')


def _bootstrap_darwin():
    _install_xcode_devtools()
    _install_homebrew()


def _bootstrap_in(_dir):
    msg = "Bootstrapping..."
    logger.info(msg)

    os_bootstrap = _get_bootstrap_for_this_os()
    os_bootstrap()

    snix_dir = os.path.join(SYS_HOME, _dir)
    _config = setup_snix_in(snix_dir)
    logger.info(msg + 'Done!')
    return _config


def _write_user_manifest(config):
    msg = 'Writing user manifest...'
    my_manifest_repo = os.path.join(snix_config[KEY_SNIX_USER_MANIFEST_DIR], SYS_USER.replace('.', '_') + '_snix')
    _create_dir(msg, my_manifest_repo)

    my_manifest_repo_git = os.path.join(my_manifest_repo, '.git')
    if not os.path.exists(my_manifest_repo_git):
        try:
            logger.info(msg + "Initializing a git repo in %s where you can manage your config" % my_manifest_repo)
            subprocess.check_call(
                ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'init'],
                stdin=None, shell=False)
        except subprocess.CalledProcessError as e:
            abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))

    _manifest = os.path.join(my_manifest_repo, MY_SNIX_FILE_NAME)
    if not os.path.exists(_manifest):
        logger.info("Committing your first ever configuration to %s" % _manifest)
        with open(_manifest, 'w') as f:
            try:
                json.dump({'config': config}, f, indent=2, sort_keys=True)
                subprocess.check_call(
                            ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'add', _manifest], stdin=None, shell=False)
                subprocess.check_call(
                            ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'commit', '-m', "Initial configuration commit", _manifest], stdin=None, shell=False)
            except subprocess.CalledProcessError as e:
                abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
    else:
        if os.path.getsize(_manifest) == 0:
            abort(_manifest+"is empty. Cannot update")
        with open(_manifest, 'r') as f:
            # TODO what if the file is empty.

            data = json.load(f)
            read_config = data['config']

        if cmp(config, read_config) != 0:
            read_config.update(config)
            with open(_manifest, 'w') as f:
                json.dump(data, f, indent=2, sort_keys=True)
            try:
                subprocess.check_call(['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'diff'], stdin=None, shell=False)
            except subprocess.CalledProcessError as e:
                abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))

    config[KEY_SNIX_MY_MANIFEST_DIR] = my_manifest_repo
    return config


def _configure_git(email):
    msg = "Configuring git..."
    try:
        subprocess.check_call(
            ['git', 'config', '--global', 'user.email', email], stdin=None, shell=False)
        output = subprocess.check_output(['git', 'config', '--get', 'user.email', email], stdin=None, shell=False)
        logger.info(msg+"Set global user email to:%s" % output)
    except subprocess.CalledProcessError as e:
        abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))

    logger.info(msg+'Done!')


if __name__ == "__main__":
    print("           _      \n" +
          " ___ _ __ (_)_  __\n" +
          "/ __| '_ \| \ \/ /\n" +
          "\__ \ | | | |>  <\n" +
          "|___/_| |_|_/_/\_\.........Setup your *nix environment!\n")

    logger.info("-------->>Hi! there. Let's get started!")

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--install_dir_name',
                        help="Name for the installation directory ($HOME/<install_dir_name>) "
                             "which will hold your code and configs")
    parser.add_argument('-g', '--github_user', help='Your github username')
    parser.add_argument('-e', '--email', help='Your email address')
    args = parser.parse_args()
    if not args.install_dir_name:
        args.install_dir_name = raw_input(
            "Please enter a directory name to create in $HOME[%s]:" % DEFAULT_INSTALL_DIR_NAME) \
                                or DEFAULT_INSTALL_DIR_NAME
    if not args.github_user:
        args.github_user = raw_input('Please enter your github username:')
    if not args.email:
        args.email = raw_input('Please enter your email address:')

    snix_config = {KEY_GITHUB_USER: args.github_user, KEY_EMAIL: args.email}
    snix_config.update(_bootstrap_in(args.install_dir_name))  # Runs the bootstrap and updates the config.
    _configure_git(snix_config[KEY_EMAIL])
    _write_user_manifest(snix_config)

    logger.info("-------->>We're now ready to install things.")

    my_snix_manifest = os.path.join(snix_config[KEY_SNIX_MY_MANIFEST_DIR], MY_SNIX_FILE_NAME)

    #logger.info("Please review {0} and start installation by running the following command \n'snix run {0}'".format(my_snix_manifest))
    # while True:
    #     choice = raw_input("Proceed with installation(yes/no)?[yes]").lower() or 'yes'
    #     if choice in ['no', 'n']:
    #
    #         break
    #     elif choice in ['yes', 'y']:
    #         logger.info("Running 'snix %s" % my_snix_manifest)
    #         break

    logger.info("-------->>Done!")
    # TODO: extract all the subprocess stuff into a method.
    # TODO: validate email address.
    # TODO: path is not working. make sure it's also what is outpu at the end of th script.

