# fava_investor

Fava_investor aims to be a comprehensive set of reports, analyses, and tools for
investments, for Beancount and Fava (personal finance software). It is developed as a
collection of modules, with each module offering a Fava plugin, a Beancount library, and
a Beancount based CLI (command line interface).

Interactivity and visualization are key for investing reports and tools, and hence the
primary focus is on Fava, even though all modules will aim to have all three interfaces.

Current modules:
- Visual, tree structured asset allocation by class
- Asset allocation by account
- Tax loss harvestor
- Cash drag analysis

More modules including investment performance are in development.

![Screenshot: TLH](./screenshot.png)
![Screenshot: Asset Allocation](./screenshot-assetalloc.png)

See screenshots [here](https://github.com/redstreet/fava_investor) if not visible above.

## Installation via pip
```bash
pip install fava-investor
```

### Running fava_investor
Add this to your beancount source, and start up fava as usual:
```
2000-01-01 custom "fava-extension" "fava_investor.fava_investor" "{}"
```

You should now see an 'Investor' link in the sidebar in fava. For more on how to
configure the extension, see the included `huge-example.beancount`.
