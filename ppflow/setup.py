from setuptools import setup, find_packages

setup(
    name="ppflow",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click",
        "pandas",
        "numpy",
        "scikit-learn",
        "torch"
    ],
    entry_points={
        "console_scripts": [
            "ppflow=ppflow.cli.main:app"
        ]
    }
)
