# fava-investor
Investment related extension for fava/beancount (personal finance software).

The goal is to develop a comprehensive set of reports and tools related to investments
for fava. See [design.md](design.md) for more.

It currently has two modules: a simple asset allocation (by account), and a tax loss
harvester:
![Screenshot](./screenshot.png)

# Install fava-investor

## Install locally

In the folder of your beancount journal file
```bash
git clone https://github.com/redstreet/fava-investor.git
```

## Install via pip to use extension
```bash
git clone https://github.com/redstreet/fava-investor.git
pip install ./fava-investor
```

## Install via pip to develop extension
```bash
git clone https://github.com/redstreet/fava-investor.git
pip install -e ./fava-investor
```


