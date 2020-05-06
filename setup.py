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
        'beancount>=2.2.3',
        'fava>=1.13',
        'argh>=0.23.3',
        'argcomplete>=1.11.1',
        'tabulate>=0.8.3'
    ],
    zip_safe=False,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Financial and Insurance Industry',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Office/Business :: Financial :: Accounting',
        'Topic :: Office/Business :: Financial :: Investment',
    ],
)
