import pathlib
from setuptools import setup, find_packages
import re

def get_long_description():
    with open('README.md') as f:
        return re.sub('!\[(.*?)\]\(docs/(.*?)\)', r'![\1](https://github.com/mara/mara-schema/raw/master/docs/\2)', f.read())

def static_files() -> [str]:
    module_path = pathlib.Path('mara_schema')
    files = []
    for p in module_path.glob('ui/static/**/*'):
        if p.is_file():
            files.append(str(p.relative_to(module_path)))
    return files


setup(
    name='mara-schema',
    version='1.1.0',

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
    package_data={'mara_schema': static_files()},

    author='Mara contributors',
    license='MIT',

    entry_points={},
)
