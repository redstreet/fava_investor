#!/usr/bin/env python3
# Description: CLI tools

import tabulate
tabulate.PRESERVE_WHITESPACE = True

def pretty_print_table(rtypes, rrows):
    headers = [i[0] for i in rtypes]
    print(tabulate.tabulate(rrows, 
        headers=headers[1:],
        tablefmt='simple'))


def pretty_print_table_bare(rrows):
    print(tabulate.tabulate(rrows, tablefmt='simple'))
