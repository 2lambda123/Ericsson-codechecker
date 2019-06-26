#
# -----------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -----------------------------------------------------------------------------

"""diff_remote function test.

Test the compraison of two remote (in the database) runs.
"""

from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import os
import re
import subprocess
import unittest

from codeCheckerDBAccess_v6.ttypes import CompareData, DiffType, \
    ReportFilter, Severity, ReviewStatus, RunHistoryFilter

from libtest import env
from libtest.debug_printer import print_run_results
from libtest.thrift_client_to_db import get_all_run_results


def get_severity_level(name):
    """
    Convert severity level from the name to value.
    """
    return Severity._NAMES_TO_VALUES[name]


class DiffRemote(unittest.TestCase):

    def setUp(self):

        # TEST_WORKSPACE is automatically set by test package __init__.py .
        test_workspace = os.environ['TEST_WORKSPACE']

        test_class = self.__class__.__name__
        print('Running ' + test_class + ' tests in ' + test_workspace)

        # Get the test configuration from the prepared int the test workspace.
        self.test_cfg = env.import_test_cfg(test_workspace)

        # Get the clang version which is tested.
        self._clang_to_test = env.clang_to_test()

        # Get the test project configuration from the prepared test workspace.
        self._testproject_data = env.setup_test_proj_cfg(test_workspace)
        self.assertIsNotNone(self._testproject_data)

        # Setup a viewer client to test viewer API calls.
        self._cc_client = env.setup_viewer_client(test_workspace)
        self.assertIsNotNone(self._cc_client)

        # Get the CodeChecker cmd if needed for the tests.
        self._codechecker_cmd = env.codechecker_cmd()

        # Get the run names which belong to this test.
        # Name order matters from __init__ !
        run_names = env.get_run_names(test_workspace)

        runs = self._cc_client.getRunData(None, None, 0)
        self._test_runs = [run for run in runs if run.name in run_names]

        # There should be at least two runs for this test.
        self.assertIsNotNone(runs)
        self.assertNotEqual(len(runs), 0)
        self.assertGreaterEqual(len(runs), 2)

        # Name order matters from __init__ !
        self._base_runid = self._test_runs[0].runId
        self._new_runid = self._test_runs[1].runId
        self._update_runid = self._test_runs[2].runId

        self._url = env.parts_to_url(self.test_cfg['codechecker_cfg'])

        self._env = self.test_cfg['codechecker_cfg']['check_env']

    def test_get_diff_checker_counts(self):
        """
        Test diff result types for new results.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.NEW)

        diff_res = self._cc_client.getCheckerCounts([base_run_id],
                                                    None,
                                                    cmp_data,
                                                    None,
                                                    0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        # core.CallAndMessage is the new checker.
        test_res = {"core.NullDereference": 4}
        self.assertDictEqual(diff_dict, test_res)

    def test_get_diff_checker_counts_core_new(self):
        """
        Test diff result types for new core checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.NEW)
        report_filter = ReportFilter(checkerName=["*core*"])
        diff_res = self._cc_client.getCheckerCounts([base_run_id],
                                                    report_filter,
                                                    cmp_data,
                                                    None,
                                                    0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        # core.CallAndMessage is the new checker.
        test_res = {"core.NullDereference": 4}
        self.assertDictEqual(diff_dict, test_res)

    def test_get_diff_res_count_new_no_base(self):
        """
        Count the new results with no filter and no baseline
        run ids.
        """
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.NEW)

        diff_res = self._cc_client.getRunResultCount([],
                                                     None,
                                                     cmp_data)
        # No differences.
        self.assertEqual(diff_res, 0)

    def test_get_diff_results_new(self):
        """
        Get the new results with no filter.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.NEW)

        diff_res = self._cc_client.getRunResults([base_run_id],
                                                 500,
                                                 0,
                                                 [],
                                                 None,
                                                 cmp_data,
                                                 False)
        # 4 new core.NullDereference issues.
        self.assertEqual(len(diff_res), 4)

    def test_get_diff_results_resolved(self):
        """
        Get the resolved results with no filter.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.RESOLVED)

        diff_res = self._cc_client.getRunResults([base_run_id],
                                                 500,
                                                 0,
                                                 [],
                                                 None,
                                                 cmp_data,
                                                 False)
        # 5 resolved core.CallAndMessage
        self.assertEqual(len(diff_res), 5)

    def test_get_diff_checker_counts_core_resolved(self):
        """
        Test diff result types for resolved core checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        report_filter = ReportFilter(checkerName=["*core*"])
        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.RESOLVED)
        diff_res = self._cc_client.getCheckerCounts([base_run_id],
                                                    report_filter,
                                                    cmp_data,
                                                    None,
                                                    0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        # Resolved core checkers.
        test_res = {'core.CallAndMessage': 5}
        self.assertDictEqual(diff_dict, test_res)

    def test_get_diff_results_unresolved(self):
        """
        Get the unresolved results with no filter.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        diff_res = self._cc_client.getRunResults([base_run_id],
                                                 500,
                                                 0,
                                                 [],
                                                 None,
                                                 cmp_data,
                                                 False)
        self.assertEqual(len(diff_res), 25)

    def test_get_diff_checker_counts_core_unresolved(self):
        """
        Test diff result types for resolved unix checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        report_filter = ReportFilter(checkerName=["*core*"])
        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)
        diff_res = self._cc_client.getCheckerCounts([base_run_id],
                                                    report_filter,
                                                    cmp_data,
                                                    None,
                                                    0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        # Unresolved core checkers.
        test_res = {'core.StackAddressEscape': 3, 'core.DivideZero': 10}
        self.assertDictContainsSubset(test_res, diff_dict)

    def test_get_diff_res_count_unresolved(self):
        """
        Count the unresolved results with no filter.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        base_count = self._cc_client.getRunResultCount([base_run_id],
                                                       None,
                                                       None)
        print("Base run id: %d", base_run_id)
        print("Base count: %d", base_count)

        base_run_res = get_all_run_results(self._cc_client, base_run_id)

        print_run_results(base_run_res)

        new_count = self._cc_client.getRunResultCount([new_run_id],
                                                      None,
                                                      None)
        print("New run id: %d", new_run_id)
        print("New count: %d", new_count)

        new_run_res = get_all_run_results(self._cc_client, new_run_id)

        print_run_results(new_run_res)

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        diff_res = self._cc_client.getRunResultCount([base_run_id],
                                                     None,
                                                     cmp_data)

        self.assertEqual(diff_res, 25)

    def test_get_diff_res_count_unresolved_filter(self):
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        filter_severity_levels = [{"MEDIUM": 1}, {"LOW": 6},
                                  {"HIGH": 18}, {"STYLE": 0},
                                  {"UNSPECIFIED": 0}, {"CRITICAL": 0}]

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        for level in filter_severity_levels:
            for severity_level, test_result_count in level.items():
                sev = get_severity_level(severity_level)
                sev_filter = ReportFilter(severity=[sev])

                diff_result_count = self._cc_client.getRunResultCount(
                    [base_run_id], sev_filter, cmp_data)

                self.assertEqual(test_result_count, diff_result_count)

    def test_get_diff_checker_counts_all_unresolved(self):
        """
        Test diff result types for all unresolved checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        diff_res = self._cc_client.getCheckerCounts([base_run_id],
                                                    None,
                                                    cmp_data,
                                                    None,
                                                    0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        # All unresolved checkers.
        test_res = {'unix.Malloc': 1,
                    'cplusplus.NewDelete': 5,
                    'deadcode.DeadStores': 6,
                    'core.StackAddressEscape': 3,
                    'core.DivideZero': 10}
        self.assertDictContainsSubset(diff_dict, test_res)

    def test_get_diff_severity_counts_all_unresolved(self):
        """
        Test diff result types for all unresolved checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        sev_res = self._cc_client.getSeverityCounts([base_run_id],
                                                    None,
                                                    cmp_data)
        test_res = {Severity.HIGH: 18,
                    Severity.LOW: 6,
                    Severity.MEDIUM: 1}
        self.assertDictEqual(sev_res, test_res)

    def test_get_diff_severity_counts_all_new(self):
        """
        Test diff result types for all unresolved checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.NEW)

        sev_res = self._cc_client.getSeverityCounts([base_run_id],
                                                    None,
                                                    cmp_data)
        test_res = {Severity.HIGH: 4}
        self.assertDictEqual(sev_res, test_res)

    def test_get_diff_new_review_status_counts(self):
        """
        Test diff result types for all unresolved checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.NEW)

        res = self._cc_client.getReviewStatusCounts([base_run_id],
                                                    None,
                                                    cmp_data)

        test_res = {ReviewStatus.UNREVIEWED: 4}
        self.assertDictEqual(res, test_res)

    def test_get_diff_unres_review_status_counts(self):
        """
        Test diff result types for all unresolved checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        res = self._cc_client.getReviewStatusCounts([base_run_id],
                                                    None,
                                                    cmp_data)

        test_res = {ReviewStatus.UNREVIEWED: 25}
        self.assertDictEqual(res, test_res)

    def test_get_diff_res_review_status_counts(self):
        """
        Test diff result types for all unresolved checker counts.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.RESOLVED)

        res = self._cc_client.getReviewStatusCounts([base_run_id],
                                                    None,
                                                    cmp_data)

        print(res)
        test_res = {ReviewStatus.UNREVIEWED: 4,
                    ReviewStatus.FALSE_POSITIVE: 1}
        self.assertDictEqual(res, test_res)

    def test_get_diff_res_types_resolved(self):
        """
        Test diff result types for resolved results.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.RESOLVED)

        diff_res = self._cc_client.getCheckerCounts([base_run_id],
                                                    None,
                                                    cmp_data,
                                                    None,
                                                    0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        test_res = {'core.CallAndMessage': 5}
        self.assertDictEqual(diff_dict, test_res)

    def test_get_diff_res_types_unresolved(self):
        """
        Test diff result types for unresolved results with no filter
        on the api.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        diff_res = \
            self._cc_client.getCheckerCounts([base_run_id],
                                             None,
                                             cmp_data,
                                             None,
                                             0)
        diff_dict = dict((res.name, res.count) for res in diff_res)

        test_res = {'unix.Malloc': 1,
                    'cplusplus.NewDelete': 5,
                    'deadcode.DeadStores': 6,
                    'core.StackAddressEscape': 3,
                    'core.DivideZero': 10}
        self.assertDictEqual(diff_dict, test_res)

    def test_get_diff_res_types_unresolved_filter(self):
        """
        Test diff result types for unresolved results with filter.
        """
        base_run_id = self._base_runid
        new_run_id = self._new_runid

        diff_res_types_filter = self._testproject_data[self._clang_to_test][
            'diff_res_types_filter']

        cmp_data = CompareData(runIds=[new_run_id],
                               diffType=DiffType.UNRESOLVED)

        for level in diff_res_types_filter:
            for checker_name, test_result_count in level.items():
                checker_filter = ReportFilter(checkerName=[checker_name])
                diff_res = \
                    self._cc_client.getCheckerCounts([base_run_id],
                                                     checker_filter,
                                                     cmp_data,
                                                     None,
                                                     0)
                diff_dict = dict((res.name, res.count) for res in diff_res)

                # There should be only one result for each checker name.
                self.assertEqual(test_result_count, diff_dict[checker_name])

    def test_cmd_compare_remote_res_count_new_rgx(self):
        """Count the new results with no filter, use regex in the run name."""
        base_run_name = self._test_runs[0].name
        new_run_name = self._test_runs[1].name

        # Change test_files_blablabla to test_*_blablabla
        new_run_name = new_run_name.replace('files', '*')

        diff_cmd = [self._codechecker_cmd, "cmd", "diff",
                    "--resolved",
                    "--url", self._url,
                    "-b", base_run_name,
                    "-n", new_run_name
                    ]
        print(diff_cmd)
        out = subprocess.check_output(diff_cmd,
                                      env=self._env,
                                      cwd=os.environ['TEST_WORKSPACE'])

        # 4 disappeared core.CallAndMessage issues
        count = len(re.findall(r'\[core\.CallAndMessage\]', out))
        self.assertEqual(count, 4)

    def test_max_compound_select(self):
        """Test the maximum number of compound select query."""
        base_run_id = self._test_runs[0].runId

        report_hashes = [str(i) for i in range(0, 10000)]
        diff_res = self._cc_client.getDiffResultsHash([base_run_id],
                                                      report_hashes,
                                                      DiffType.NEW)
        self.assertEqual(len(diff_res), len(report_hashes))

    def test_diff_run_tags(self):
        """Test for diff runs by run tags."""
        run_id = self._update_runid

        def get_run_tag_id(tag_name):
            run_history_filter = RunHistoryFilter(tagNames=[tag_name])
            run_tags = self._cc_client.getRunHistory([run_id], None, None,
                                                     run_history_filter)
            self.assertEqual(len(run_tags), 1)
            return run_tags[0].id

        base_tag_id = get_run_tag_id('t1')
        new_tag_id = get_run_tag_id('t2')

        tag_filter = ReportFilter(runTag=[base_tag_id])
        cmp_data = CompareData(runIds=[run_id],
                               diffType=DiffType.NEW,
                               runTag=[new_tag_id])

        diff_res = self._cc_client.getRunResults([run_id],
                                                 500,
                                                 0,
                                                 [],
                                                 tag_filter,
                                                 cmp_data,
                                                 False)

        # 5 new core.CallAndMessage issues.
        self.assertEqual(len(diff_res), 5)

        cmp_data.diffType = DiffType.RESOLVED
        diff_res = self._cc_client.getRunResults([run_id],
                                                 500,
                                                 0,
                                                 [],
                                                 tag_filter,
                                                 cmp_data,
                                                 False)
        self.assertEqual(len(diff_res), 3)

        cmp_data.diffType = DiffType.UNRESOLVED
        diff_res = self._cc_client.getRunResults([run_id],
                                                 500,
                                                 0,
                                                 [],
                                                 tag_filter,
                                                 cmp_data,
                                                 False)
        self.assertEqual(len(diff_res), 26)
