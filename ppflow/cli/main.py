# ppflow/cli/main.py
import sys
import click  
from datahandling.scanner import scan_data
from pathlib import Path

import warnings
warnings.filterwarnings("ignore")

from datahandling.ui.renderer import render_dataset_identity
from datahandling.diagnostics.runner import run_diagnostics



@click.group()
def app():
    """PPFlow CLI."""
    pass

@app.command()
def init():
    print("PPFlow project initialized!")

@app.command()
def scan():
    print("Scanning data pipelines...")
    dataset = scan_data()

    render_dataset_identity(dataset)
   

@app.command()
@click.option("--fix", is_flag=True, help="Ask user to fix issues interactively")
@click.option("--fixall", is_flag=True, help="Automatically fix all issues")
def diagnose(fix, fixall):

    run_diagnostics(fix=fix, fixall=fixall)

@app.command()
def logs():
    print("Showing logs...")

@app.command()
def env():
    print("Python version:", sys.version)

if __name__ == "__main__":
    app()