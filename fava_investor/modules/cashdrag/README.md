# Cashdrag 

Summarizes amounts and locations (account) of cash across all your accounts, to help you
invest it.

## Installation
A Fava extension, a Beancount command line client, and a library are all included.
To install the Fava plugin, see [fava_investor](https://github.com/redstreet/fava_investor).

Command line client:
```
investor cashdrag example.bc
investor cashdrag --help
```
The command line client also uses the same Fava configuration shown below.

## Configuration

Configure Cashdrag by including the following lines in your Beancount source. Example:

```
2010-01-01 custom "fava-extension" "fava_investor" "{
  'cashdrag': {
     'accounts_pattern':         '^Assets:.*',
     'accounts_exclude_pattern': '^Assets:(Cash-In-Wallet.*|Zero-Sum)',
     'metadata_label_cash'     : 'asset_allocation_Bond_Cash'
}}"
```

The full list of configuration options is below:

#### `accounts_pattern`

Default: '^Assets'

Regex of accounts to include.

---

#### `accounts_exclude_pattern`

Default: ''

Regex of accounts to exclude. Exclusions are applied after `accounts_pattern` is applied.

---

#### `metadata_label_cash`

Default: 'asset_allocation_Bond_Cash'

Optional. If specified, consider all currencies that have this metadata set to `100`, to
be cash.
