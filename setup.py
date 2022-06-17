from os import path
from setuptools import find_packages, setup

with open(path.join(path.dirname(__file__), 'README.md')) as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name='fava_investor',
    use_scm_version=True,
    setup_requires=['setuptools_scm'],
    description='Fava extension and beancount libraries for investing',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/redstreet/fava_investor',
    author='Red S',
    author_email='redstreet@users.noreply.github.com',
    license='GPL-3.0',
    keywords='fava beancount accounting investment',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click >= 7.0',
        'beancount >= 2.3.2',
        'click_aliases >= 1.0.1',
        'fava >= 1.15',
        'packaging >= 20.3',
        'python_dateutil >= 2.8.1',
        'tabulate >= 0.8.9',
        'yfinance >= 0.1.70',
    ],
    entry_points={
        'console_scripts': [
            'ticker-util = fava_investor.util.ticker_util:cli',
            'scaled-navs = fava_investor.util.experimental.scaled_navs:scaled_navs',
            'investor = fava_investor.cli.investor:cli',
        ]
    },
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.8',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)
