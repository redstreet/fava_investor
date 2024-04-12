# Changelog

## 0.7.0 (2024-02-02)

This release brings fava_investor up to date with upstream changes in Fava. Primarily,
asset allocation by class was fixed. Thanks to contributors below.

### Fixes

- Fix assetalloc_class chart (#93) [Adriano Di Luzio]
- remove dead code for Fava <v1.18 (#91) [Jakob Schnitzer]
- hierarchy chart: remove now uneeded modifier (#90) [Jakob Schnitzer]
- libsummarizer crash in Fava (wrong pricemap) [Red S]
- build_beancount_pricemap() was missing in cli version. [Red S]


## 0.6.0 (2024-02-02)

### Improvements

- Fix to work with upstream changes (Fava 1.25+)

- Make currency regex not incorrectly match substrings (#88) [Tyler Schicke]

  This changes the currency regexes use '^<currency>$' instead of just
  matching '<currency>', so that specifying a currency only matches that
  currency exactly, instead of also matching currencies that contain the
  specified currency.
- Preserve costs during tax adjustment (#83) [korrat]

  * Preserve costs during tax adjustment

  Previously, tax adjustment discarded the cost of positions, causing
  beancount.core.convert.convert_position to miss some conversion paths
  via the cost currency. This necessitated a fallback to operating
  currencies for finding viable transitive conversions.

  With this patch, tax adjustment preserves the cost of positions.
  Therefore, the cost currency is still available for automatic detection
  of transitive conversions when computing the asset allocation.

  One important assumption is that tax adjustment only ever encounters
  costs after realization, as having a cost spec for the total cost would
  change the cost per unit. This assumption is checked via assert and has
  been manually tested without error on the multicurrency example.

  The patch leaves the fallback logic for conversion via operating
  currencies in place as an alternative when conversion via cost currency
  fails.
  * Fix lint warnings


- add --tax-burden to minimizegains. [Red S]
  Interpolate tax burden from table for a specified amount
- add config table to gains minimizer. [Red S]
- minor: sort asset allocation output. [Red S]
- minor: clean up columns in gains minimizer. [Red S]
- minor: remove prefixes in asset allocation for clearer output. [Red S]
  cli only
- minor: minimizegains: add avg and marginal tax percentage columns. [Red S]
- minor: cashdrag: add `min_threshold` option; convert to primary currency. [Red S]

### Fixes

- summarizer fail due to favapricemap vs beancount pricemap. [Red S]
- cashdrag failed with command line (only worked with fava) [Red S]

  - use beancount's convert_position, not fava
- asset_alloc_by_account to work with upstream changes. [Red S]

  - fix cost_or_value from upstream changes
- broken tests. [Red S]
- breaks with new fava versions #86. [Red S]
- print warning when skipping negative positions in asset alloc. [Red S]
- minimizegains column deletion was incorrect. [Red S]

### Other

## 0.5.0 (2022-12-25)

### Improvements

- asset allocation by class: fixed chart placement using upstream changes [Red S]


## 0.4.0 (2022-11-22)

### New

- minimizegains module. works on cli and fava. [Red S]

### Improvements

- tlh/relatetickers: rename 'tlh_partners' to 'a__tlh_partners' [Red S]
  In line with the other metadata fields, `tlh_partners` has been renamed
  to `a__tlh_partners` and is now both an input and and auto-generated
  field
- tlh/relatetickers: rename and add 'a__equivalents' [Red S]
  In line with the other metadata fields, `equivalent` has been renamed to
  `a__equivalents` and is now both an input and and auto-generated field
- tlh/relatetickers: remove tlh_partners_meta_label feature. [Red S]
  this simplifies config, and clarifies.
- tlh: removed susubstantially_identical_meta_label feature. [Red S]
  this is a simplification to provide clarity.
- tlh/relatetickers: Show only same type of TLH partners. [Red S]

### Fixes

- #79 bump fava dependency to 1.22 due to upstream filtering changes. [Red S]
- minor: spelling. [Red S]
- beancountinvestorapi open method needed to index into list. [Red S]
- ticker_util: substidentical and a__substidentical are both accepted. [Red S]
- fix (summarizer, tlh, util): rename "similar" to "identical" [Red S]

  IRS uses substantially identical
- libminimizegains: couldn't use arbitrary currencies. [Red S]

### Other

- relatetickers: unit test. [Red S]
- pythonanywhere update.bash. [Red S]
- pythonanywhere example asset alloc looks nicer now. [Red S]
- pythonanywhere example is not too shabby now. #72 #24. [Red S]
- ci: fix test. [Red S]
- refactor: add tlh substantially identical based wash sale example. [Red S]
- refactor: rename similars to idents. [Red S]
- ci: flake ignore. [Red S]
- doc/tlh: specifying substantially identical, and equivalent metadata. [Red S]
- refactor: remove 'substidenticals' meta label. [Red S]

  use only a__substidenticals, which is both an input field, and gets
  overwritten
- ci: flake. [Red S]
- ci: flake. [Red S]
- doc: feature todos for minimizegains. [Red S]
- doc: minimizegains README.txt. [Red S]
- wip: minimizegains. [Red S]


## 0.3.0 (2022-08-07)
### New

- new module: summarizer to summarize and display reasonably arbitrary tables of account
  and commodity metadata
- Modules now respect GUI context (time interval). For example, see what your cashdrag
  was or what you could have TLH'ed on any arbitrary day in the past
- experimental utility: scaled mutual fund NAV estimator: estimate a mutual fund's NAV
  based on current intra-day value of its corresponding NAV

### Improvements

- add footer to pretty_print. cashdrag uses it.
- assetalloc_class: read fava config from beancount file for command line.
- cashdrag: read fava config from beancount file for command line.
- cli: consolidated all modules into `investor` command.
- enable fava context and filters. Fixes #36. Also upstream favaledger.
- pager via click.
- ticker-util now puts asset allocation info it can find.
- tlh: comma betweeen similars and alts lists.
- tlh: read fava config from beancount file for command line.
- better example (still WIP)
- pythonanywhere config and example

### Fixes

- fix: use filtered entries in query_shell.
- fix: #61 Show welcome message on initial screen when no modules are selected.
- fix/favainvestorapi: #67 get_account_open() returns empty.

### Other

- several upgrades for fava 1.22 [Aaron Lindsay, Red S]
- several doc upgrades
- several refactors
- refactor: ticker-util cleanup; _ to - in options.
- test: fix assetalloc_class pytests.
- wip: demo example #72.


## 0.2.5 (2022-06-12)
### New
- ticker-util. See [here](https://groups.google.com/g/beancount/c/eewOW4HQKOI)

### Improvements
- tlh: allow specifying tlh_partner meta label. [Red S]
- tlh: also consider substantially similar tickers in wash sale computations. [Red S]
- tlh docs. [Red S]
- tlh new feature: wash_ids. [Red S]
- tlh wash_id: configurable metadata label, bugfixes. [Red S]
- tlh: what not to buy now includes similars. [Red S]
- rename env var to BEAN_COMMODITIES_FILE. [Red S]


### Other

- build: requirements via pigar. [Red S]
- doc: create changelog + gitchangelog config. [Red S]
- doc: examples. [Red S]
- doc: README upate. Relaxed requirements. [Red S]
- refactor: favainvestorapi cleanup. [Red S]
- refactor: upgrade deprecated asyncio code. [Red S]
- ticker-util: and ticker-relate: major refactor into a single utility. [Red S]
- ticker-util: available keys. [Red S]
- ticker-util: click: relate subcommand group. [Red S]
- ticker_util: feature: add from commodities file. [Red S]
- ticker-util: feature add: include undeclared. [Red S]
- ticker-util: features: specify metadata, appends as cli args. [Red S] also: empty substsimilar metadata is excluded
- ticker-util: header. [Red S]
- ticker-util: moved to click. [Red S]


## 0.2.4 (2022-05-12)


### Other

- tlh: bug in wash sale (31 vs 30 days) [Red S]
- Flake. [Red S]
- Pythonpackage workflow. [Red S]
- . [Red S]
- tlh: sort main table by harvestable losses. [Red S]

## 0.2.3 (2022-05-11)


### Improvements

- TLH: screenshot update. [Red S]
  - Example update for article. [Red S]
  - tlh: html notes. [Red S]
  - tlh: rename subst to alt. [Red S]
  - tlh: clarify safe to harvest date. [Red S]
  - tlh: sort by harvestable loss. [Red S]
  - tLh: add built in options for account_field. [Red S]
  - tlh README. [Red S]
  - add subst column to TLH "Losses by Commodity" [Red S]
  - Show tlh alternate. [Red S]
  - tlh: show get one but leaf. [Red S]


## 0.2.2 (2022-04-27)
### Improvements
- Add long/short info to TLH. [Red S]
- Asset allocation by class: add multi currency support #32. [Red S]
  - requires all operating currencies to be specified

### Fixes
- Fix for upstream changes: Use `url_for` instead of `url_for_current` [Aaron Lindsay]
- Unbreak account_open_metadata. #35 [Martin Michlmayr]
- Support fava's newly modified querytable macro. [Aaron Lindsay]

### Other
- README updates, including #55. [Red S]
- Example account hierarchy update. [Red S]
- Fix assetalloc_class pytests. [Red S]
- tlh fix pytests. [Red S]

## 0.2.1 (2021-01-10)
- Macro asset_tree fix to make toggling work in fava v1.15 onwards. [Red S]
- Table update to include footer (can't merge this until fava release) [Red S]
