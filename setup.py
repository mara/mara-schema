from setuptools import setup, find_packages

setup(
    name='mara-schema',
    version='0.1.0',

    description='Mapping of DWH database tables to business entities, attributes & metrics in Python, with automatic creation of flattened tables',

    install_requires=[
        "flask",
        "graphviz",
        "mara-page",
        "sqlalchemy"
    ],
    tests_require=['pytest'],

    packages=find_packages(),

    author='Mara contributors',
    license='MIT',

    entry_points={},
)
