#!/usr/bin/env python3
# Description: CLI tools

import tabulate
tabulate.PRESERVE_WHITESPACE = True


def pretty_print_table(rtypes, rrows, **kwargs):
    headers = [i[0] for i in rtypes]
    options = {'tablefmt': 'simple'}
    options.update(kwargs)
    print(tabulate.tabulate(rrows, headers=headers, **options))


def pretty_print_table_bare(rrows):
    print(tabulate.tabulate(rrows, tablefmt='simple'))
