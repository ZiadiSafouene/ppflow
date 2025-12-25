# ppflow/cli/main.py
import sys
import click  # optional, can also use argparse
from datahandling.scanner import scan_data
import warnings
warnings.filterwarnings("ignore")
from datahandling.ui.renderer import render_dataset_identity


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
def diagnose():
    print("Running diagnostics...")

@app.command()
def logs():
    print("Showing logs...")

@app.command()
def env():
    print("Python version:", sys.version)

if __name__ == "__main__":
    app()