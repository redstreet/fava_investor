# fava-investor

Fava-Investor aims to be a comprehensive set of reports, analyses, and tools for
investments, for Beancount/Fava (personal finance software). It is developed as a
collection of modules, with each module offering a Fava plugin, a Beancount library, and
a Beancount based CLI (command line interface).

Interactivity and visualization are key for investing reports and tools, and hence the
primary focus is on Fava, even though all modules will have all three interfaces.

It currently has two modules: asset allocation (by class, by account), and a tax loss
harvester, with more in development.  See [design.md](design.md) for more.
*Contributions welcome!*

![Screenshot](./screenshot.png)

# Installation

### Install locally

In the folder of your beancount journal file
```bash
git clone https://github.com/redstreet/fava-investor.git
```

### Install via pip to use extension
```bash
git clone https://github.com/redstreet/fava-investor.git
pip install ./fava-investor
```

### Install via pip to develop extension
```bash
git clone https://github.com/redstreet/fava-investor.git
pip install -e ./fava-investor
```
