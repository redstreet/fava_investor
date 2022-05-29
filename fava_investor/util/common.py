#!/usr/bin/env python3
import os
from beancount import loader


commodities_file = os.getenv('COMMODITIES_FILE')
def load_file(cf=commodities_file):
    if cf is None:
        print(f"Commodities file not specified. Set the environment variable COMMODITIES_FILE or use --cf",
                file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(cf):
        print(f"File not found: {cf}", file=sys.stderr)
        sys.exit(1)
    return loader.load_file(cf)
