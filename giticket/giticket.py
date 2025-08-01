# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals

import argparse
import io
import re
import subprocess
import sys

import six

underscore_split_mode = 'underscore_split'
regex_match_mode = 'regex_match'


def update_commit_message(filename, regex, mode, format_string, divider, divider_offset):
    with io.open(filename, 'r+') as fd:
        contents = fd.readlines()
        commit_msg = contents[0].rstrip('\r\n')
        # Check if we can grab ticket info from branch name.
        branch = get_branch_name()

        # Bail if commit message already contains tickets
        if any(re.search(regex, content) for content in contents):
            return

        tickets = re.findall(regex, branch)
        if tickets:
            if mode == underscore_split_mode:
                tickets = [branch.split(six.text_type('_'))[0]]

            if divider:
                # Example: Expand PRO123 -> PRO-123
                tickets = [divider not in t and f"{t.strip()[0:divider_offset]}{divider}{t.strip()[divider_offset:]}" or t.strip() for t in tickets]
            else:
                tickets = [t.strip() for t in tickets]

            new_commit_msg = format_string.format(
                ticket=tickets[0], tickets=', '.join(tickets),
                commit_msg=commit_msg
            )

            contents[0] = six.text_type(new_commit_msg + "\n")
            fd.seek(0)
            fd.writelines(contents)
            fd.truncate()


def get_branch_name():
    # Only git support for right now.
    return subprocess.check_output(
        [
            'git',
            'rev-parse',
            '--abbrev-ref',
            'HEAD',
        ],
    ).decode('UTF-8')


def main(argv=None):
    """This hook saves developers time by prepending ticket numbers to commit-msgs.
    For this to work the following two conditions must be met:

        - The ticket format regex specified must match.
        - The branch name format must be <ticket number>_<rest of the branch name>
        - Setting 'divider' and 'divider_offset' can be used to expand PROJECT123 to PROJECT-123 or PROJECT::123
    """
    parser = argparse.ArgumentParser()
    # Required #
    parser.add_argument('filenames', nargs='+')
    # Optional #
    parser.add_argument('--regex')
    parser.add_argument('--format')
    parser.add_argument('--divider')
    parser.add_argument('--divider_offset', type=int, default=3)
    parser.add_argument('--mode', nargs='?', const=underscore_split_mode,
                        default=underscore_split_mode,
                        choices=[underscore_split_mode, regex_match_mode])
    args = parser.parse_args(argv)
    regex = args.regex or r'[A-Z]+-\d+'  # noqa
    format_string = args.format or '{ticket} {commit_msg}'  # noqa
    divider_offset = args.divider_offset
    update_commit_message(args.filenames[0], regex, args.mode, format_string, args.divider, divider_offset)


if __name__ == '__main__':
    sys.exit(main())
