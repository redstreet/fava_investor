import re

from beancount.core.account import parent, parents
from fava.core import FavaLedger, Tree
from fava.core.tree import TreeNode


def get_closed_tree_with_value_accounts_only(accapi, config) -> Tree:
    ledger: FavaLedger = accapi.ledger
    tree = ledger.root_tree_closed
    accounts_to_keep = _get_value_accounts_and_parents(
        accapi.ledger.accounts, config.get("accounts_patterns", [".*"])
    )
    _filter_tree(tree, accounts_to_keep)
    return tree


def get_value_accounts(accounts, patterns):
    result = set()
    for account in accounts:
        if _is_value_account(account, patterns):
            result.add(account)
    return result


def _remove_account_from_tree(tree: Tree, account: str):
    if account not in tree or account == "":
        return
    node = tree[account]
    for child in list(node.children):
        _remove_account_from_tree(tree, child.name)

    _remove_from_parent(account, node, tree)
    _reduce_parents_balances(account, node, tree)

    del tree[account]


def _get_value_accounts_and_parents(accounts: dict, patterns):
    result = get_value_accounts(accounts, patterns)

    for value_acc in list(result):
        for p in parents(value_acc):
            result.add(p)
    return result


def _filter_tree(tree, accounts_to_keep):
    for account in list(tree.keys()):
        if account not in accounts_to_keep:
            _remove_account_from_tree(tree, account)


def _reduce_parents_balances(account, node, tree):
    for parent_account in parents(account):
        parent_node: TreeNode = tree[parent_account]
        parent_node.balance_children.add_inventory(-node.balance)


def _remove_from_parent(account, node, tree):
    parent_account = parent(account)
    if parent_account is not None:
        parent_node: TreeNode = tree[parent_account]
        parent_node.children.remove(node)


def _is_value_account(account, patterns):
    for pattern in patterns:
        if re.match(pattern, account):
            return True
    return False
