from os import path
from setuptools import find_packages, setup

with open(path.join(path.dirname(__file__), 'README.md')) as readme:
    LONG_DESCRIPTION = readme.read()

setup(
    name='fava_investor',
    version='0.1',
    description='Investor: fava extension and beancount libraries for investing',
    long_description=LONG_DESCRIPTION,
    url='https://github.com/redstreet/fava_investor',
    author='Red S',
    author_email='redstreet@users.noreply.github.com',
    license='GPL-3.0',
    keywords='fava beancount accounting investment',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'beancount>=2.2.3',
        'fava>=1.13',
        'argcomplete>=1.11.1'
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GPLv3',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)
