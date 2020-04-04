# Desired feature list

The goal is to develop a comprehensive set of reports and tools related to investments
for fava. This document contains list of potential features that we would like to
consider for implementation.

## Reports

### Asset allocation: By asset class:
- port [this](https://github.com/redstreet/beancount_asset_allocation) to fava
- Pie chart, hierarchical
  - Reference chart
  - top level alone chart (to simplify complex portfolios)?

- Tax adjusted

### Asset allocation: By account:
- like the current one

### Asset allocation: Tax Treatment:
- taxable, tax-deferred, etc.
- configure using parent account or metadata

### IRR (internal rate of return):
- across specified portfolio
- drillable down to account-level and holding-leve
- advanced: show tax drag (difficult to quantify)

### Net worth:
- across time (redundant?)
- show split of contributions, income (dividends, gains, etc.), and appreciation
  - filterable (by account?)
  - across arbitrary time periods
  - related to IRR above

### Savings rate:
- absolute number across time
- as %age of gross, net

### Summary stats:
- number of unique funds owned
- number of brokerage accounts


## Tools

### Cash drag analysis:
- cash as percentage of portfolio, and where it is

### Tax loss harvester:
- suck this in

### Rebalancing:
- consider plugging into a rebalancing tool
  ([example1](https://github.com/AlexisDeschamps/portfolio-rebalancer),
  [example2](https://github.com/hoostus/lazy_rebalance))

