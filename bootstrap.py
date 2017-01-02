import ConfigParser
import argparse
import os
import platform
import re
import subprocess
import logging
import socket
import sys

SYS_HOME = os.environ['HOME']

DEFAULT_INSTALL_DIR = os.path.join(SYS_HOME, 'lab')
SNIX_EXECUTABLE = 'snix'
SNIX_CODE_DIR = '_' + SNIX_EXECUTABLE
SNIX_CONF_FILE = os.path.join(os.sep, "usr", "local", "etc", SNIX_EXECUTABLE + os.extsep + "conf")

KEY_SNIX_HOME = 'snix.home'

logger = logging.getLogger(__name__)
logging.basicConfig(format='%(asctime)s-%(levelname)s-%(message)s', datefmt='%Y%d%m %I:%M:%S %p', level=logging.DEBUG)


def abort(msg):
    logger.error(" -Aborting!- %s" % msg)
    sys.exit(1)


# noinspection PyBroadException
def network_up():
    """Checks if the network is up. Returns a tuple(True/False, message)"""
    msg = "Network is "
    try:
        host = socket.gethostbyname("www.google.com")
        socket.create_connection((host, 80), 2)
        return True, msg + 'Up.'
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
def clone_repo_into(_dir):
    """Clones the snix source code git repo"""
    _msg = "Cloning snix source code repo."
    if not os.path.exists(_dir):
        abort("%s does not exist!" % _msg)

    snix_repo = os.path.join(_dir, SNIX_CODE_DIR)
    snix_repo_git = os.path.join(snix_repo, '.git')

    if not os.path.exists(snix_repo):
        try:
            subprocess.check_call(['git', 'clone', "https://github.com/yaise/snix.git", snix_repo], stdin=None,
                                  shell=False)
        except subprocess.CalledProcessError as e:
            abort(_msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
    else:
        if os.path.exists(snix_repo_git):
            logger.info(_msg + "Found %s! Will update." % snix_repo)
            try:
                subprocess.check_call(['git', "--git-dir=%s" % snix_repo_git, "--work-tree=%s" % snix_repo, 'pull'],
                                      stdin=None, shell=False)
            except subprocess.CalledProcessError as e:
                abort(_msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
            return
        else:
            logger.info(_msg + "Directory exists but no repository found. Deleting %s" % snix_repo)
            os.rmdir(snix_repo)

    logger.info(_msg + 'Done!')


@precondition(network_up)
def install_xcode_devtools():
    """" Installs Xcode developer tools without any UI intervention.
    Credit:
    github.com/timsutton/osx-vm-templates/blob/ce8df8a7468faa7c5312444ece1b977c1b2f77a4/scripts/xcode-cli-tools.sh """

    msg = "XCode Developer Tools..."
    if os.path.exists(os.path.join(os.sep, 'Library', 'Developer', 'CommandLineTools')):
        logger.info(msg + "Already installed!")
        return

    tmp_file = "/tmp/.com.apple.dt.CommandLineTools.installondemand.in-progress"
    with open(tmp_file, 'a'):
        os.utime(tmp_file, None)

    try:
        logger.info(msg + 'Searching')
        list_updates = subprocess.Popen(['softwareupdate', '-l'], stdout=subprocess.PIPE)
        find_xcode_cli = subprocess.Popen(['grep', "*.*Command Line"], stdin=list_updates.stdout,
                                          stdout=subprocess.PIPE)
        result = find_xcode_cli.communicate()[0]
        logger.info(result)
        if result is None:
            abort(msg + "Not found.")
        tool_name = result.split('*')[1].strip()
        list_updates.stdout.close()

        logger.info(msg + 'Installing ' + tool_name)
        install = subprocess.Popen(['softwareupdate', '-i', '--verbose', tool_name], stdin=None, stdout=subprocess.PIPE)
        while True:
            output = install.stdout.readline()
            if output == '' and install.poll() is not None:
                break
            else:
                sys.stdout.write(output)
                sys.stdout.flush()
    except subprocess.CalledProcessError as e:
        abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))


def bootstrap_darwin():
    install_xcode_devtools()


def create_dir(_dir):
    if not os.path.exists(_dir):
        logger.info("Creating dir:" + _dir)
        os.mkdir(_dir)
    else:
        logger.info("%s already exists." % _dir)
        if not os.access(_dir, os.R_OK | os.W_OK | os.X_OK):
            abort("%s permissions should be rwx or 777")


def bootstrap_in(_dir):
    def _get_bootstrap_for_this_os():
        return {
            'Darwin': bootstrap_darwin
        }.get(platform.system())

    create_dir(_dir)

    os_bootstrap = _get_bootstrap_for_this_os()
    os_bootstrap()

    clone_repo_into(_dir)

    logger.info("Bootstrapping...Done!")
    return _dir


# def _write_user_manifest(config):
#     msg = 'Writing user manifest...'
#     my_manifest_repo = os.path.join(snix_config[KEY_SNIX_USER_MANIFEST_DIR], SYS_USER.replace('.', '_') + '_snix')
#     _create_dir(my_manifest_repo)
#
#     my_manifest_repo_git = os.path.join(my_manifest_repo, '.git')
#     if not os.path.exists(my_manifest_repo_git):
#         try:
#             logger.info(msg + "Initializing a git repo in %s where you can manage your config" % my_manifest_repo)
#             subprocess.check_call(
#                 ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'init'],
#                 stdin=None, shell=False)
#         except subprocess.CalledProcessError as e:
#             abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
#
#     _manifest = os.path.join(my_manifest_repo, MY_SNIX_FILE_NAME)
#     if not os.path.exists(_manifest):
#         logger.info("Committing your first ever configuration to %s" % _manifest)
#         with open(_manifest, 'w') as f:
#             try:
#                 json.dump({'config': config}, f, indent=2, sort_keys=True)
#                 subprocess.check_call(
#                     ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'add',
#                      _manifest], stdin=None, shell=False)
#                 subprocess.check_call(
#                     ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'commit', '-m',
#                      "Initial configuration commit", _manifest], stdin=None, shell=False)
#             except subprocess.CalledProcessError as e:
#                 abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
#     else:
#         if os.path.getsize(_manifest) == 0:
#             abort(_manifest + "is empty. Cannot update")
#         with open(_manifest, 'r') as f:
#             # TODO what if the file is empty.
#
#             data = json.load(f)
#             read_config = data['config']
#
#         if cmp(config, read_config) != 0:
#             read_config.update(config)
#             with open(_manifest, 'w') as f:
#                 json.dump(data, f, indent=2, sort_keys=True)
#             try:
#                 subprocess.check_call(
#                     ['git', "--git-dir=%s" % my_manifest_repo_git, "--work-tree=%s" % my_manifest_repo, 'diff'],
#                     stdin=None, shell=False)
#             except subprocess.CalledProcessError as e:
#                 abort(msg + "{0} exited with error code{1}".format(e.cmd, e.returncode))
#
#     config[KEY_SNIX_MY_MANIFEST_DIR] = my_manifest_repo
#     return config


def add_snix_to_path(_snix_home):
    _snix_executable = os.path.join(_snix_home, SNIX_CODE_DIR, SNIX_EXECUTABLE)
    _usr_local_bin_snix = os.path.join(os.sep, "usr", "local", "bin", SNIX_EXECUTABLE)
    if not os.path.islink(_usr_local_bin_snix):
        logger.info("Adding {src} to path({dst})".format(src=_snix_executable, dst=_usr_local_bin_snix))
        os.symlink(_snix_executable, _usr_local_bin_snix)
    else:
        logger.info("{src} already exists in path({dst})".format(src=_snix_executable, dst=_usr_local_bin_snix))
    logger.info("Configuring Path...Done!")


def write_snix_config(_snix_home):
    _config = ConfigParser.RawConfigParser()
    _config.add_section("config")
    _config.set("config", KEY_SNIX_HOME, _snix_home)
    _snix_conf_file_path = os.path.join(os.sep, "usr", "local", "etc", SNIX_CONF_FILE)
    with open(_snix_conf_file_path, 'wb') as f:
        _config.write(f)
    logger.info("Snix configuration written in %s" % _snix_conf_file_path)
    logger.info("Writing config file...Done!")


if __name__ == "__main__":
    print("           _      \n" +
          " ___ _ __ (_)_  __\n" +
          "/ __| '_ \| \ \/ /\n" +
          "\__ \ | | | |>  <\n" +
          "|___/_| |_|_/_/\_\.........Setup your *nix environment!\n")

    logger.info("-------->>Hi! there. Let's get started!")

    _parser = argparse.ArgumentParser()
    _parser.add_argument('-i', '--install_dir_name',
                         help="Name for the installation directory ($HOME/<install_dir_name>) "
                              "which will hold your code and configs")
    _args = _parser.parse_args()
    if not _args.install_dir_name:
        _args.install_dir_name = raw_input(
            "Give me a directory to set stuff up in. Press Enter to accept the default[%s]:"
            % DEFAULT_INSTALL_DIR) or DEFAULT_INSTALL_DIR

    snix_home = bootstrap_in(_args.install_dir_name)

    add_snix_to_path(snix_home)

    write_snix_config(snix_home)

    logger.info("-------->>We're now ready to initialize snix.")
    logger.info("Please run the following command : snix init")
    logger.info("-------->>Thanks for Snix-ing! ")
