import re

from beancount.core.account import parent, parents
from fava.core import FavaLedger, Tree
from fava.core.tree import TreeNode
from fava_investor.common.favainvestorapi import FavaInvestorAPI


def get_closed_tree_with_value_accounts_only(accapi: FavaInvestorAPI, config) -> Tree:
    ledger: FavaLedger = accapi.ledger
    tree = ledger.root_tree_closed
    accounts_to_keep = get_value_accounts_and_parents(accapi.ledger.accounts, config.get('value', ['.*']))
    filter_tree(tree, accounts_to_keep)
    return tree


def remove_account_from_tree(tree: Tree, account: str):
    if account not in tree or account == '':
        return
    node = tree[account]
    for child in list(node.children):
        remove_account_from_tree(tree, child.name)

    remove_from_parent(account, node, tree)
    reduce_parents_balances(account, node, tree)

    del tree[account]


def get_value_accounts_and_parents(accounts: dict, patterns):
    result = set()
    for account in accounts:
        if is_value_account(account, patterns):
            result.add(account)
            for p in parents(account):
                result.add(p)
    return result


def filter_tree(tree, accounts_to_keep):
    for account in list(tree.keys()):
        if account not in accounts_to_keep:
            remove_account_from_tree(tree, account)


def reduce_parents_balances(account, node, tree):
    for parent_account in parents(account):
        parent_node: TreeNode = tree[parent_account]
        parent_node.balance_children.add_inventory(-node.balance)


def remove_from_parent(account, node, tree):
    parent_account = parent(account)
    if parent_account is not None:
        parent_node: TreeNode = tree[parent_account]
        parent_node.children.remove(node)


def is_value_account(account, patterns):
    for pattern in patterns:
        if re.match(pattern, account):
            return True
    return False


