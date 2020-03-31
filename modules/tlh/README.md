# Fava/Beancount Tax Loss Harvester
Tax loss harvester plugin for Fava (Beancount personal finance software).

Reports the set of lots that can be tax loss harvested from your beancount input file.
Also determines which of them would trigger wash sales. Example:

![TLH screenshot](./readme-screenshot.png)

The example above shows that 350,100 USD of losses can be harvested by selling the rows
listed. However, 1 BNCT of that would be considered a wash sale and will not be
allowable. It also shows the account and quantities of each commodity to sell total sale
proceeds (1,051,900 USD) if all the recommended lots were sold.

A Fava extension and a beancount command line client are both included.

## Beancount Command Line Client

Requires python3, argcomplete, and tabulate:
```pip3 install argcomplete tabulate```

Example invocation:
```./tlh.py example.bc -a "Assets:Investments:Taxable" --wash-pattern "Assets:Investments"```

```--brief``` displays just the summary. See ```./tlh.py --help``` for all options.


## Fava Installation
Clone the source to a directory (eg: extensions/fava/tlh relative to your beancount
source).

Include this in your beancount source:

```2010-01-01 custom "fava-extension" "extensions.fava.tlh" ""```

## Configuration

Configure TLH through your beancount sources. Example:

```
2010-01-01 custom "fava-extension" "extensions.fava.tlh" "{
  'account_field': 'account',
  'accounts_pattern': 'Assets:Investments:Taxable',
  'loss_threshold': 50,
  'wash_pattern': 'Assets:Investments',
}"
```

### `account_field`
Default: LEAF(account)

This string is a part of the beancount query. If you want to see the entire account
name, set this to 'account'.

---

### `accounts_pattern`
Default: ''

Regex of the set of accounts to search over for tax loss harvesting opportunities.
This allows you to exclude your tax advantaged and other non-investment accounts.

---

### `loss_threshold`
Default: 1

Losses below this threshold will be ignored. Useful to filter out minor TLH
opportunities.

---

### `wash_pattern`
Default: ''

Regex of the set of accounts to search over for possible wash sales. This allows you to
include your tax advantaged and all investment accounts.

---

## Limitations

- Partial wash sales, or cases where it is not obvious as to how to match the purchases
  and sales, are not displayed due to their
  [complexity.](https://fairmark.com/investment-taxation/capital-gain/wash/wash-sale-matching-rules/)

- Booking via specific identification of shares is assumed on all taxable accounts. This
  translates to "STRICT" booking in beancount.


TODO:
- show if a loss generated would be long term or short term
