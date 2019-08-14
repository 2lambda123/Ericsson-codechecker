# -------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -------------------------------------------------------------------------

"""Parse the skip list file."""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import fnmatch
import re

from codechecker_common.logger import get_logger

LOG = get_logger('system')


class SkipListHandler(object):
    """Parse the skip list file format.

    For every skip line in the skip list a regex is generated
    which is matched for a given file path to check if
    it should be skipped or not.

    Order of the lines in the skip file matter!
    Go from more specific to more global rules like:
    +*/3pp_other/lib/not_to_skip.cpp
    -*/3pp_other/*

    Skiplist file format:

    -/skip/all/source/in/directory*
    -/do/not/check/this.file
    +/dir/check.this.file
    -/dir/*
    """

    def __init__(self, skip_file_content=""):
        """Parse the lines of the skip file."""
        self.__skip = []

        self.__skip_file_lines = [line.strip() for line
                                  in skip_file_content.splitlines()
                                  if line.strip()]

        valid_lines = self.__check_line_format(self.__skip_file_lines)
        self.__gen_regex(valid_lines)

    def __gen_regex(self, skip_lines):
        """Generate a regular expression from the given skip lines
        and collect them for later match.

        The lines should be checked for validity before generating
        the regular expressions.
        """
        for skip_line in skip_lines:
            rexpr = re.compile(
                fnmatch.translate(skip_line[1:].strip() + '*'))
            self.__skip.append((skip_line, rexpr))

    def __check_line_format(self, skip_lines):
        """Check if the skip line is given in a valid format.

        Returns the list of valid lines.
        """
        valid_lines = []
        for line in skip_lines:
            if len(line) < 2 or line[0] not in ['-', '+']:
                LOG.warning("Skipping malformed skipfile pattern: %s", line)
                continue

            valid_lines.append(line)

        return valid_lines

    @property
    def skip_file_lines(self):
        """List of the lines from the skip file without changes."""
        return self.__skip_file_lines

    def overwrite_skip_content(self, skip_lines):
        """Clean out the already collected skip regular expressions
        and rebuilds the list from the given skip_lines.
        """
        self.__skip = []
        valid_lines = self.__check_line_format(skip_lines)
        self.__gen_regex(valid_lines)

    def should_skip(self, source):
        """Check if the given source should be skipped.

        Match the given source path to the processed regex list.
        """
        if not self.__skip:
            return False

        for line, rexpr in self.__skip:
            if rexpr.match(source):
                sign = line[0]
                return sign == '-'
        return False
