from setuptools import setup, find_packages

setup(
    name='mara-metadata',
    version='0.0.1',

    description='Opinionated lightweight DWH schema management framework',

    install_requires=[
        "flask>=0.12",
        "graphviz>=0.6",
        "mara-page>=1.1.0",
        "lxml"
    ],
    tests_require=['pytest'],

    dependency_links=[
        'https://github.com/mara/mara-page/archive/1.1.0.zip#egg=mara-page-1.1.0'
    ],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
)
