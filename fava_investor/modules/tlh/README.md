# Fava/Beancount Tax Loss Harvester
Tax loss harvester plugin for Fava (Beancount personal finance software).

Reports the set of lots that can be tax loss harvested from your beancount input file.
Also determines which of them would trigger wash sales. Example:

![Screenshot: TLH](../../../screenshot.png)

The example above shows a summary of what can be tax-loss harvested currently. This
includes the total harvestable loss, and the sale value required to harvest the loss.
Detailed and summary views of losses by commodity and lots is shown. Losses that would
not be allowable due to wash sales are marked.

A Fava extension and a Beancount command line client are both included.

## Beancount Command Line Client

Requires python3, argcomplete, and tabulate:
```pip3 install argcomplete tabulate```

Example invocation:
```
./tlh.py example.bc -a "Assets:Investments:Taxable" --wash-pattern "Assets:Investments"
```

`--brief` displays just the summary. See `./tlh.py --help` for all options.


## Fava Installation

See [fava_investor](https://github.com/redstreet/fava_investor)

## Configuration

Configure TLH by including the following lines in yourbeancount source. Example:

```
2010-01-01 custom "fava-extension" "fava_investor" "{
  'tlh' : {
    'account_field': 'account',
    'accounts_pattern': 'Assets:Investments:Taxable',
    'loss_threshold': 50,
    'wash_pattern': 'Assets:Investments',
   },
   ...
}"
```

The full list of configuration options is below:

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

Optionally, include the `tlh_substitutes` metadata in your commodity declarations. The
string you provide simply gets summarized into the table above if available (not shown
in the example), serving as an easy reminder for you. For example:

```
2010-01-01 commodity VTI
  tlh_substitutes: "VOO"
```

## Limitations

- Partial wash sales, or cases where it is not obvious as to how to match the purchases
  and sales, are not displayed due to their
  [complexity.](https://fairmark.com/investment-taxation/capital-gain/wash/wash-sale-matching-rules/)

- Booking via specific identification of shares is assumed on all taxable accounts. This
  translates to "STRICT" booking in beancount.

#### Disclaimer
None of the above is or should be construed as financial, tax, or other advice.
