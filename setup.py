from setuptools import setup, find_packages
import re

def get_long_description():
    with open('README.md') as f:
        return re.sub('!\[(.*?)\]\(docs/(.*?)\)', r'![\1](https://github.com/mara/mara-schema/raw/master/docs/\2)', f.read())

setup(
    name='mara-schema',
    version='1.0.1',

    description='Mapping of DWH database tables to business entities, attributes & metrics in Python, with automatic creation of flattened tables',
    long_description=get_long_description(),
    long_description_content_type='text/markdown',

    url = 'https://github.com/mara/mara-schema',

    install_requires=[
        "flask",
        "graphviz",
        "mara-page",
        "sqlalchemy"
    ],
    python_requires='>=3.6',

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
)
