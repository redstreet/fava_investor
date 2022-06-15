# Asset Allocation

Understanding the asset allocation of a portfolio is important. This module reports your
current portfolio's asset allocation, to an arbitrary asset class hierarchy and depth of
your choice.

## Installation
A Fava extension, a Beancount command line client, and a library are all included.
To install the Fava plugin, see [fava_investor](https://github.com/redstreet/fava_investor).

Command line client:
```
investor assetalloc-class example.beancount
```
The command line client also uses the same Fava configuration shown below.

## Configuration

### Options
Options are declared using a custom `"fava-extension"` directive, which is used both by
the Fava plugin and the CLI, like so:

```
        2010-01-01 custom "fava-extension" "fava_investor" "{
          'asset_alloc_by_class' : {
              'accounts_patterns': ['Assets:(Investments|Banks)'],
              'skip-tax-adjustment': True,
          }}"
```

The full list of configuration options is below:

#### `accounts_pattern`

Regex specifying a set of accounts to consider.

#### `skip_tax_adjustment`

When set to False, ignore the `asset_allocation_tax_adjustment` metadata declarations.

### Metadata Declarations for Commodities

The percentage of each asset class for each commodity is specified in the commodity
metadata, like so:

```
2010-01-01 commodity BMUT
 asset_allocation_equity_international: 60
 asset_allocation_bond: 40
```


The only requirement is that the metadata field name begins with the prefix
`asset_allocation_`, and has a number for its value that is a percentage, corresponding
to the percentage of the commodity belonging to that asset class. The set of all asset
classes for a commodity should add up to a 100. When they do not, the reporter will pad
the remaining with the 'unknown' class.

What comes after that prefix in the commodity metadata is arbitrary, which is what
allows you to nest your allocation hierarchy as deep as you would like, separated b
`_`s.

More examples:

```
2010-01-01 commodity BOND
 asset_allocation_bond_municipal: 80
 asset_allocation_bond_treasuries: 20
```

```
2010-01-01 commodity ANOTHERBOND
 asset_allocation_bond: 100
```

```
2010-01-01 commodity SP500
 asset_allocation_equity_domestic: 100
```

```
2010-01-01 commodity USD
 asset_allocation_bond_cash: 100
```

### Metadata Declarations for Accounts

Optionally, the percentage by which an entire account should be scaled for tax purposes
is specified by the `asset_allocation_tax_adjustment` metadata in an account's `open`
directive like so:

```
2010-01-01 open Assets:Investments:Tax-Deferred:Retirement
  asset_allocation_tax_adjustment: 55
```

## Example Output
```
$ ./asset_allocation.py example.beancount --dump-balances-tree
```
Output:
```
asset_type                amount    percentage
----------------------  --------  ------------
Total                    158,375        100.0%
 equity                  124,862         78.8%
  equity_international   112,000         70.7%
 bond                     29,838         18.8%
  bond_municipal           1,838          1.2%
 realestate                3,675          2.3%

Account balances:
`-- Assets                       
    `-- Investments                700 BNCT
        |-- Tax-Deferred         
        |   `-- Retirement          55 COFE
        `-- Taxable              
            `-- XTrade             190 COFE
```

Asset allocations are displayed hierarchically. Percentages and amounts include the
children. For example, the 'bond' percentage and amount above includes municipal bonds.

