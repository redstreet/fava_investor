#!/usr/bin/env python3
"""Main command line interface for investor"""

import click
# import fava_investor.modules.assetalloc_account as assetalloc_account
import fava_investor.modules.assetalloc_class.assetalloc_class as assetalloc_class
import fava_investor.modules.cashdrag.cashdrag as cashdrag
import fava_investor.modules.summarizer.summarizer as summarizer
import fava_investor.modules.tlh.tlh as tlh
import fava_investor.modules.minimizegains.minimizegains as minimizegains
import fava_investor.modules.performance.performance as performance


@click.group()
def cli():
    pass


# cli.add_command(assetalloc_account.assetalloc_account)
cli.add_command(assetalloc_class.assetalloc_class)
cli.add_command(cashdrag.cashdrag)
cli.add_command(summarizer.summarizer)
cli.add_command(tlh.tlh)
cli.add_command(minimizegains.minimizegains)
cli.add_command(performance.performance)


if __name__ == '__main__':
    cli()
