## Intro
Asset allocation analysis tool for Beancount (Personal accounting software).

Understanding the asset allocation of a portfolio is important. This script reports your
current portfolio's asset allocation.


## Configuration

You specify a set of accounts to consider (using a regex pattern).

You also specify the percentage of each asset class for each commodity in your accounts
as a part of its metadata in your Beancount ledger, like so:

```
2010-01-01 commodity BMUT
 asset_allocation_equity_international: 60
 asset_allocation_bond: 40
```

The only requirement is that the metadata field name begins with 'asset_allocation_',
and has a number for its value that is a percentage, corresponding to the percentage of
the commodity belonging to that asset class. The set of all asset classes for a
commodity should add up to a 100. When they do not, the reporter will pad the remaining
with the 'unknown' class.

Examples to illustrate:

```
2010-01-01 commodity BOND
 asset_allocation_bond_municipal: 80
 asset_allocation_bond_treasuries: 20
```

```
2010-01-01 commodity SP500
 asset_allocation_equity_domestic: 100
```

```
2010-01-01 commodity USD
 asset_allocation_bond_cash: 100
```

### Hierarchical Asset Allocation

What comes after that prefix in the commodity metadata is arbitrary and is left up to
you. Keep in mind that asset allocation can be hierarchical. As an example: equity,
bonds at the top level; equity could be domestic or international; domestic equity could
be individual company stocks, or funds, and so on. Given that, it makes sense to
organize your asset allocation data hierarchically, separated by the '_' character (or
any other valid character of your choice).


## Example:
Run example by executing:
```
$ ./asset_allocation.py example.beancount --accounts "Assets:Investments:" --dump-balances-tree
```
Output:
```
Asset Type         Percentage    Amount
---------------  ------------  --------
total                  100.0%     2,750
 bond                   48.2%     1,325
  municipal             19.1%       525
 equity                 46.4%     1,275
  international         43.6%     1,200
 realestate              5.5%       150

Account balances:
`-- Assets                  
    `-- Investments             7 BNCT
        |-- Brokerage           1 BNCT
        `-- XTrade              2 BNCT
                               10 COFE
```

Asset allocations are displayed hierarchically. Percentages and amounts include the
children. For example, the 'bond' percentage and amount above includes municipal bonds.

