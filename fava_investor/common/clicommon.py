#!/usr/bin/env python3
"""CLI tools common library"""

import click
import csv
import tabulate
tabulate.PRESERVE_WHITESPACE = True


def pretty_print_table(title, rtypes, rrows, footer=None, **kwargs):
    title_out = click.style(title + '\n', bg='green', fg='white')
    if footer:
        rrows += [(i[1] for i in footer)]

    if rrows:
        headers = [i[0] for i in rtypes]
        options = {'tablefmt': 'simple'}
        options.update(kwargs)
        return click.style(title_out + tabulate.tabulate(rrows, headers=headers, **options) + '\n\n')
    else:
        return click.style(title_out + '(empty table)' + '\n\n')


def pretty_print_table_bare(rrows):
    print(tabulate.tabulate(rrows, tablefmt='simple'))


def write_table_csv(filename, table):
    """ Write table to csv file """
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        headers = [i[0] for i in table[1][0]]
        writer.writerow(headers)

        for row in table[1][1]:
            writer.writerow(row)
