# Performance
_Show XIRR of investments_

## Introduction
This modules shows the XIRR of chosen investments and the summary of all the investments chosen.

## Using this module
- Accounts contains account name
- XIRR contains XIRR of investments

## Limitations
XIRR are calculated using a maximum of 10 newton iterations for speed, so while the output is close to the final value, the accuracy cannot be guaranteed.

## Example configuration:
```
  'performance' : {
     'account_field': 'account',
     'accounts_pattern': 'Assets:Investments',
     'accuracy': 2,
  },
```
