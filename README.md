# fava_investor

Fava_investor aims to be a comprehensive set of reports, analyses, and tools for
investments, for Beancount/Fava (personal finance software). It is developed as a
collection of modules, with each module offering a Fava plugin, a Beancount library, and
a Beancount based CLI (command line interface).

Interactivity and visualization are key for investing reports and tools, and hence the
primary focus is on Fava, even though all modules will have all three interfaces.

It currently has two modules: asset allocation (by class, by account), and a tax loss
harvester, with more in development.  See [design.md](design.md) for more.
*Contributions welcome!*

![Screenshot: TLH](./screenshot.png)
![Screenshot: Asset Allocation](./screenshot-assetalloc.png)

# Installation

### Install locally

In the folder of your beancount journal file
```bash
pip3 install fava argh argcomplete
git clone https://github.com/redstreet/fava_investor.git

# Assuming you did this in the same directory of your beancount source, invoke the fava
# extension using the line below, given the actual module lives in a subdirectory that
# is also named fava_investor:
# 2010-01-01 custom "fava-extension" "fava_investor.fava_investor" "{...}"
```

### Install via pip to use extension
```bash
git clone https://github.com/redstreet/fava_investor.git
pip install ./fava_investor
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
