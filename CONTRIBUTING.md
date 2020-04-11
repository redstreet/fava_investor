### Pre-requisities

If you want to develop or contribute to fava_investor, make sure you have Python 3 (with
pip). Install beancount and fava:

`pip install fava`

### Running fava_investor
```
mkdir dev
cd dev
git clone https://github.com/redstreet/fava_investor.git # or point to your fork
cd fava_investor
fava example.bc
```

Then, point your browser to: http://localhost:5000/test

As shown in the screenshots on the main page, several Investor links should appear in
Fava.

### Contributing code
Fork the repo on github and submit pull requests.

See Philosophy section below before you contribute

### Contribution Guidelines

Each module must include a Fava plugin, a Beancount library, and a Beancount based CLI
(command line interface). APIs in `fava_investor/common/{favainvestorapi.py,
beancountinvestorapi.py}` allow for easily developing these three interfaces to the
library. The goal is to keep fava or beancount specific code neatly separated.

Take a look at the `tlh` module to understand how to approach this. It is divided into three files:
- `libtlh.py`: main library, agnostic to Fava/beancount. Calls the functions it needs via common/*investorapi
- `tlh.py`: command line client that calls the library
- fava_investor/`__init.py__`: fava interface that calls the library

Of course, tests and html templates exist in their own files.
