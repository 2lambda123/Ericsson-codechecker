# -------------------------------------------------------------------------
#                     The CodeChecker Infrastructure
#   This file is distributed under the University of Illinois Open Source
#   License. See LICENSE.TXT for details.
# -------------------------------------------------------------------------
"""
Contains functions to format and pretty-print data from two-dimensional arrays.
"""
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import json
from operator import itemgetter

# The supported formats the users should specify. (This is not an exhaustive
# list of ALL formats available.)
USER_FORMATS = ['rows', 'table', 'csv', 'json']


def twodim_to_str(format_name, keys, rows,
                  sort_by_column_number=None, rev=False,
                  separate_footer=False):
    """
    Converts the given two-dimensional array (with the specified keys)
    to the given format.
    """
    if sort_by_column_number is not None:
        rows.sort(key=itemgetter(sort_by_column_number), reverse=rev)

    all_rows = rows
    if keys is not None and keys:
        all_rows = [keys] + rows

    if format_name == 'rows':
        return twodim_to_rows(rows)
    elif format_name == 'table' or format_name == 'plaintext':
        # TODO: 'plaintext' for now to support the 'CodeChecker cmd' interface.
        return twodim_to_table(all_rows, True, separate_footer)
    elif format_name == 'csv':
        return twodim_to_csv(all_rows)
    elif format_name == 'dictlist':
        return twodim_to_dictlist(keys, rows)
    elif format_name == 'json':
        return json.dumps(twodim_to_dictlist(keys, rows))
    else:
        raise ValueError("Unsupported format")


def twodim_to_rows(lines):
    """
    Prints the given rows with minimal formatting.
    """

    str_parts = []

    # Count the column width.
    widths = []
    for line in lines:
        for i, size in enumerate([len(x) for x in line]):
            while i >= len(widths):
                widths.append(0)
            if size > widths[i]:
                widths[i] = size

    # Generate the format string to pad the columns.
    print_string = " "
    for i, width in enumerate(widths):
        if i == 0 or i == len(widths) - 1:
            print_string += "{" + str(i) + "} "
        else:
            print_string += "{" + str(i) + ":" + str(width) + "} "
    if not print_string:
        return
    print_string = print_string[:-1]

    # Print the actual data.
    for i, line in enumerate(lines):
        try:
            str_parts.append(print_string.format(*line))
        except IndexError:
            raise TypeError("One of the rows have a different number of "
                            "columns than the others")

    return '\n'.join(str_parts)


def twodim_to_table(lines, separate_head=True, separate_footer=False):
    """
    Pretty-prints the given two-dimensional array's lines.
    """

    str_parts = []

    # Count the column width.
    widths = []
    for line in lines:
        for i, size in enumerate([len(str(x)) for x in line]):
            while i >= len(widths):
                widths.append(0)
            if size > widths[i]:
                widths[i] = size

    # Generate the format string to pad the columns.
    print_string = ""
    for i, width in enumerate(widths):
        print_string += "{" + str(i) + ":" + str(width) + "} | "
    if not print_string:
        return
    print_string = print_string[:-3]

    # Print the actual data.
    str_parts.append("-" * (sum(widths) + 3 * (len(widths) - 1)))
    for i, line in enumerate(lines):
        try:
            str_parts.append(print_string.format(*line))
        except IndexError:
            raise TypeError("One of the rows have a different number of "
                            "columns than the others")
        if i == 0 and separate_head:
            str_parts.append("-" * (sum(widths) + 3 * (len(widths) - 1)))
        if separate_footer and i == len(lines) - 2:
            str_parts.append("-" * (sum(widths) + 3 * (len(widths) - 1)))

    str_parts.append("-" * (sum(widths) + 3 * (len(widths) - 1)))

    return '\n'.join(str_parts)


def twodim_to_csv(lines):
    """
    Pretty-print the given two-dimensional array's lines in CSV format.
    """

    str_parts = []

    # Count the columns.
    columns = 0
    for line in lines:
        if len(line) > columns:
            columns = len(line)

    print_string = ""
    for i in range(columns):
        print_string += "{" + str(i) + "},"

    if not print_string:
        return
    print_string = print_string[:-1]

    # Print the actual data.
    for line in lines:
        try:
            str_parts.append(print_string.format(*line))
        except IndexError:
            raise TypeError("One of the rows have a different number of "
                            "columns than the others")

    return '\n'.join(str_parts)


def twodim_to_dictlist(key_list, lines):
    """
    Pretty-print the given two-dimensional array's lines into a JSON
    object list. The key_list acts as the "header" of the table, specifying the
    keys to use in the resulting object.

    This function expects values to be the same number as the length of
    key_list, and that the order of values in a line corresponds to the order
    of keys.
    """

    res = []
    for line in lines:
        res.append({key: value for (key, value) in zip(key_list, line)})

    return res


def dictlist_to_twodim(key_list, dictlist, key_convert=None):
    """
    Converts the given list of dict objects to a two-dimensional array.

    If key_convert is specified, the resulting array will have the converted
    strings in its "header" row. key_list and key_convert must correspond with
    each other in order.
    """

    if not key_convert:
        lines = [key_list]
    else:
        lines = [key_convert]

    for d in dictlist:
        lines.append([d[key] for key in key_list])

    return lines
