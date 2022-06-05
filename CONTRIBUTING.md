*Contributions welcome!* See [design.md](design.md) or the issues in github for more on
some of the areas to contribute.

### Pre-requisities
If you want to develop or contribute to fava_investor, make sure you have Python 3 (with
pip). Install beancount and fava:

`pip install fava`

# Installation

### Install locally

In the folder of your beancount journal file
```bash
pip3 install fava
git clone https://github.com/redstreet/fava_investor.git

# Assuming you did this in the same directory of your beancount source, invoke the fava
# extension using the line below, given the actual module lives in a subdirectory that
# is also named fava_investor:
# 2010-01-01 custom "fava-extension" "fava_investor.fava_investor" "{...}"
```
### Install via pip to develop extension
```bash
git clone https://github.com/redstreet/fava_investor.git
pip install -e ./fava_investor
```

### Running fava_investor
```
cd fava_investor
fava example.beancount
# or:
fava huge-example.beancount
```
Then, point your browser to: http://localhost:5000/test

As shown in the screenshots above, a link to Investor should appear in Fava.

### Problems

If you see this in the Fava error page:
`"Importing module "fava_investor" failed."`

That usually means the module was not able to be loaded. Try running python3
interactively and typing:

`import fava_investor.fava_investor`

That should succeed, or tell you what the failure was.


# Contributing code
Fork the repo on github and submit pull requests.

See Philosophy section below before you contribute

### Contribution Guidelines

Each module should include a Fava plugin, a Beancount library, and a Beancount based CLI
(command line interface). APIs in `fava_investor/common/{favainvestorapi.py,
beancountinvestorapi.py}` allow for easily developing these three interfaces to the
library. The goal is to keep the modules agnostic to whether they are running within a
beancount or fava context.

Take a look at the `tlh` module to understand how to approach this. It is divided into three files:
- `libtlh.py`: main library, agnostic to Fava/beancount. Calls the functions it needs via common/*investorapi
- `tlh.py`: command line client that calls the library
- fava_investor/`__init.py__`: fava interface that calls the library

Of course, tests and html templates exist in their own files.
