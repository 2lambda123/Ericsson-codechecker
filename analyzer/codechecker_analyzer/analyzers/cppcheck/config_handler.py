# -------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -------------------------------------------------------------------------
"""
Config handler for Cppcheck analyzer.
"""
from .. import config_handler
from ..config_handler import CheckerState

class CppcheckConfigHandler(config_handler.AnalyzerConfigHandler):
    """
    Configuration handler for Cppcheck analyzer.
    """
    def initialize_checkers(self, analyzer_context, checkers, cmdline_enable=..., enable_all=False):
        """
        Set all the default checkers to disabled. This will ensure that
        --enable=all will not run with all the possible checkers
        """
        super().initialize_checkers(analyzer_context, checkers, cmdline_enable, enable_all)

        # Set all the default checkers to disabled. This will ensure that
        # --enable=all will not run with all the possible checkers
        for checker_name, data in self.checks().items():
            if data[0] == CheckerState.default:
                self.set_checker_enabled(checker_name, enabled = False)
        return