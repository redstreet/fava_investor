# Metadata Summarizer

Define arbitrary tables to summarize and view account metadata, and commodity metadata.
For example, say you want to view the customer service phone numbers for each of your
investment and banking accounts, which you have stored in the account metadata like so
in your beancount file:

  ```
  2015-01-01 open Assets:Banks:Checking USD
      customer_service_phone: "1-555-123-4567"
  ```

and so forth for each account. You can view a neat summary table in fava or on the
command line by including these lines:

  ```
  2010-01-01 custom "fava-extension" "fava_investor" "{
    'summarizer': [
      { 'title' : 'Customer Service Phone Number',
        'directive_type'  : 'accounts',
        'acc_pattern' : '^Assets:(Investments|Banks)',
        'col_labels': [ 'Account', 'Phone_number'],
        'columns' : [ 'account', 'customer_service_phone'],
        'sort_by' : 0,
      }]}"
  ```
  
Other metadata (eg: transactions or postings) are not supported.

## Installation
A Fava extension, a Beancount command line client, and a library are all included.
To install the Fava plugin, see [fava_investor](https://github.com/redstreet/fava_investor).

Command line client:
```
investor summarizer example.beancount
investor summarizer --help              # for all options
```

The command line client also uses the same Fava configuration shown below.

## Configuration
The full list of configuration options is below:

#### `title`

Table title.

---
#### `directive_type`

For each table, this can be `accounts` or `commodities`. Each table can summarize
metadata of either accounts or commodities.

---
#### `acc_pattern`

When the `accounts` directive_type is chosen, the set of accounts to include in the
table, specified as a regex.

---
#### `col_labels`

Column titles. No spaces allowed. This is optional. If not specified, the metadata keys
are used instead.

---
#### `columns`

Metadata keys for each column.


---
#### `sort_by`

Column number to sort table by.

---
#### `meta_prefix`

Specifying `meta_prefix` (instead of `columns`) for account metadata will display all
metadata beginning with the prefix.

---
#### `meta_skip`

Skip displaying accounts that contain specified metadata keys

---
#### `no_footer`

Do not display footer

---
#### `sort_reverse`

Self explanatory

---
The following are special values for 'columns', when 'directive_type' is 'accounts':
- `account`: replace with account name
- `balance`: replace with current balance of the account

---
The following are special values for 'columns', when 'directive_type' is 'commodities':
- `ticker`:       replace with ticker
- `market_value`: replace with current market value of the commodity held

Here are two examples of handy commodity summaries to have, to be used in conjunction
with `ticker-util`, which ships with Fava Investor:

```
2010-01-01 custom "fava-extension" "fava_investor" "{
  'summarizer': [
    { 'title' : 'Commodities Summary',
      'directive_type'  : 'commodities',
      'active_only': True,
      'col_labels': [ 'Ticker', 'Type', 'Equi', 'Description', 'TLH_to', 'ER', 'Market'],
      'columns' : [ 'ticker', 'a__quoteType', 'equivalent', 'name', 'tlh_alternates', 'a__annualReportExpenseRatio', 'market_value'],
      'sort_by' : 1,
    },
    { 'title' : 'TLH: Substantially Similars and TLH Partners',
      'directive_type'  : 'commodities',
      'active_only': True,
      'col_labels': [ 'Ticker', 'Subst_Similars', 'TLH_Partners'],
      'columns' : [ 'ticker', 'a__substsimilars', 'a__tlh_partners'],
      'sort_by' : 0,
    },
   ]
 }"
```
