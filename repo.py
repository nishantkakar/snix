#!/usr/bin/env python
import shlex

from snixCore import execute, execute_in_dir_and_revert, abort
import snixLogger

logger = snixLogger.SnixLogger.logger()


class Repo:
    """Represents a repository."""

    def __init__(self, context):
        if not type(context) is dict:
            abort('Cannot clone a repo without the configuration.')
        self._context = context

    def clone(self):
        with execute_in_dir_and_revert(self._context['snix_root']):
            msg = "Cloning {0}...".format(self._context['repo_location'])
            cmd, use_shell = self._build_cmd()
            logger.info(msg + cmd)
            ret = execute(shlex.split(cmd), use_shell)
            logger.info(msg + 'StatusCode:' + str(ret))
            logger.info(msg + 'Done!')

    def _build_cmd(self):
        return "git clone " + self._context['repo_location'], False
