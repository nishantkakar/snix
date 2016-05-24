#!/usr/bin/env python
import os

import snixLogger
from snixCore import execute, execute_in_dir_and_revert, abort

logger = snixLogger.SnixLogger.logger()


class Command:
    """Represents an executable command."""

    def __init__(self, context, use_shell=False):
        if not type(context) is dict:
            abort("Cannot execute a command without the configuration.")
        self._context = context
        self._use_shell = use_shell

    def execute(self):
        command = self._context['command']
        _exec_dir = self._context['command_exec_dir']
        if not os.path.isdir(_exec_dir):
            abort("{0} is not a valid path".format(_exec_dir))
        with execute_in_dir_and_revert(_exec_dir):
            execute(command, self._use_shell)
