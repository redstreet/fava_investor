"""fava wsgi application"""
from __future__ import annotations

from fava.application import app as application

application.config["BEANCOUNT_FILES"] = [
  "/home/favainvestor/.local/lib/python3.9/site-packages/fava_investor/pythonanywhere/example.beancount"
]
