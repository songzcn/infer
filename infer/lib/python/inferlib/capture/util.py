#!/usr/bin/env python

# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os
import logging
import subprocess
import traceback

from inferlib import utils


def get_build_output(build_cmd):
    #  TODO make it return generator to be able to handle large builds
    proc = subprocess.Popen(build_cmd, stdout=subprocess.PIPE)
    (verbose_out_chars, _) = proc.communicate()
    return utils.decode(verbose_out_chars).split('\n')


def run_compilation_commands(cmds, clean_cmd):
    """runs compilation commands, and suggests a project cleaning command
    in case there is nothing to compile.
    """
    #  TODO call it in parallel
    if len(cmds) == 0:
        utils.stdout('Nothing to compile. Try running `{}` first.'
                     .format(clean_cmd))
        return os.EX_NOINPUT
    for cmd in cmds:
        if cmd.start() != os.EX_OK:
            return os.EX_SOFTWARE
    return os.EX_OK


def run_cmd_ignore_fail(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        return 'calling {cmd} failed\n{trace}'.format(
            cmd=' '.join(cmd),
            trace=traceback.format_exc())


def log_java_version():
    java_version = run_cmd_ignore_fail(['java', '-version'])
    javac_version = run_cmd_ignore_fail(['javac', '-version'])
    logging.info('java versions:\n%s%s', java_version, javac_version)


def base_argparser(description, module_name):
    def _func(group_name=module_name):
        """This creates an empty argparser for the module, which provides only
        description/usage information and no arguments."""
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument_group(
            '{grp} module'.format(grp=group_name),
            description=description,
        )
        return parser
    return _func


def clang_frontend_argparser(description, module_name):
    def _func(group_name=module_name):
        """This creates an argparser for all the modules that require
        clang for their capture phase, thus InferClang and clang wrappers"""
        parser = argparse.ArgumentParser(add_help=False)
        group = parser.add_argument_group(
            '{grp} module'.format(grp=group_name),
            description=description,
        )
        group.add_argument(
            '-hd', '--headers',
            action='store_true',
            help='Analyze code in header files',
        )
        group.add_argument(
            '--models_mode',
            action='store_true',
            dest='models_mode',
            help='Mode for computing the models',
        )
        group.add_argument(
            '--no_failures_allowed',
            action='store_true',
            dest='no_failures_allowed',
            help='Fail if at least one of the translations fails',
        )
        group.add_argument(
            '-tm', '--testing_mode',
            dest='testing_mode',
            action='store_true',
            help='Testing mode for the translation: Do not translate headers')
        group.add_argument(
            '--cxx',
            dest='cxx',
            action='store_true',
            help='Analyze C++ code, still experimental')
        group.add_argument(
            '-fs', '--frontend-stats',
            dest='frontend_stats',
            action='store_true',
            help='Output statistics about the capture phase to *.o.astlog')
        group.add_argument(
            '-fd', '--frontend-debug',
            dest='frontend_debug',
            action='store_true',
            help='Output debugging information to *.o.astlog during capture')
        return parser
    return _func


def get_clang_frontend_envvars(args):
    """Return the environment variables that configure the clang wrapper, e.g.
    to emit debug information if needed, and the invocation of the Infer
    frontend for Clang, InferClang, e.g. to analyze headers, emit stats, etc"""
    env_vars = {}
    frontend_args = []

    env_vars['INFER_RESULTS_DIR'] = args.infer_out

    return env_vars