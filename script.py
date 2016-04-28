#!/usr/bin/env python
import os
import shlex

from snixCore import execute, execute_in_dir_and_revert, abort
import snixLogger

logger = snixLogger.SnixLogger.logger()


class Script:
    """Represents an executable script."""

    def __init__(self, context):
        if not type(context) is dict:
            abort('Cannot execute a script without the configuration.')
        self._context = context

    def execute(self):
        script_path=os.path.join(self._context['snix_root'],self._context['script_location'])
        if not os.access(script_path, os.X_OK):
            abort(script_path+"is not executable!")
        # with execute_in_dir_and_revert(self._context['snix_root']):
        msg = "Executing {0}...".format(script_path)
        logger.info(msg + script_path)
        ret = execute(shlex.split(script_path), True)
        logger.info(msg + 'StatusCode:' + str(ret))
        logger.info(msg + 'Done!')

