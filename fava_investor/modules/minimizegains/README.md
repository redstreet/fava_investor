# Gains Minimizer
_Determine lots to sell to minimize capital gains taxes._

## Introduction
When partially liquidating from taxable accounts, (for example, to make a purchase, or to draw down
from one's retirement savings), capital gains are potentially generated and subject to taxation. 

Careful selection of lots to be sold will allow the tax burden to be minimized in this scenario.
This Gains Minimizer module can help. It displays a table of lots to sell, ordered by their tax
burden. By selling portfolio lots in this order, tax burden is minimized.

## Using this module
- most columns in the table are self-explanatory. The non-obvious ones are explained below
- est_tax is the estimated tax on the sale. This is computed using the '[sl]_t_tax_rate' fields in
  the configuration below
- est_tax_percent is the percentage of estimated taxes on the proceeds (market_value). This is the
  column that this table is sorted by
- cumu_proceeds is the cumulative proceeds (sum of the market_value of all rows upto and including
  this one)
- cumu_gains is the cumulative gains (sum of the gains of all rows upto and including this one)
- percent is the ratio of cumu_gains to cumu_proceeds

To use this table, look down the cumu_proceeds until the first row that exceeds the amount you wish
to liquidate. Liquidate all preceeding rows, including a partial amount of the last row until you
liquidate the amount you desire.

## Limitations
Selling in this manner does not account for Asset allocation, which the sales may cause to shift.
If maintaining constant allocation is desired, a different algorithm must be used. In addition,
such an algorithm may have to consider the tax-advantaged portions of the portfolio.


## Example configuration:
```
'minimizegains' : { 'accounts_pattern': 'Assets:Investments:Taxable',
                    'account_field': 2,
                    'st_tax_rate':   0.30,
                    'lt_tax_rate':   0.15 }
```
