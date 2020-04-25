from beancount.core.account import parent, parents

from fava_investor.modules.performance.split import get_matching_accounts


def get_balances_tree(accapi, config):
    tree = accapi.ledger.root_tree_closed
    accounts_to_keep = get_value_accounts_and_parents(tree, accapi.ledger.accounts,
                                                      config.get("accounts_pattern", "^Assets:.*"))
    filter_tree(tree, accounts_to_keep)
    return tree


def get_value_accounts_and_parents(tree, accounts, patterns):
    result = get_matching_accounts(accounts, patterns)
    ancestors = [p.name for acc in result for p in tree.ancestors(acc)]
    return result.union(ancestors)


def filter_tree(tree, accounts_to_keep):
    nodes_to_remove = [n for n in tree if n not in accounts_to_keep]
    nodes_to_remove.sort(key=lambda s: len(s), reverse=True)
    for account in nodes_to_remove:
        remove_account_from_tree(tree, account)


def remove_account_from_tree(tree, account):
    if account not in tree or not account:
        return

    node = tree[account]
    remove_from_parent(account, node, tree)
    reduce_parents_balances(account, node, tree)
    del tree[account]


def remove_from_parent(account, node, tree):
    parent_account = parent(account)
    if parent_account:
        parent_node = tree[parent_account]
        parent_node.children.remove(node)


def reduce_parents_balances(account, node, tree):
    for parent_account in parents(account):
        parent_node = tree[parent_account]
        parent_node.balance_children.add_inventory(-node.balance)
        parent_node.balance_children.add_inventory(-node.balance_children)
