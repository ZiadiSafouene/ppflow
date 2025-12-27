import shutil
from pathlib import Path
from .tabular import run_tabular_diagnostics
import click

SEVERITY_STYLE = {
    "low": {"fg": "blue"},
    "info": {"fg": "cyan"},
    "warning": {"fg": "yellow"},
    "medium": {"fg": "yellow"},
    "high": {"fg": "red"},
    "critical": {"fg": "red", "bold": True},
}

def display_issues(issues):
    click.secho("\nDetected issues:\n", bold=True)

    for idx, issue in enumerate(issues, 1):
        style = SEVERITY_STYLE.get(issue.severity, {})

        click.secho(f"[{idx}] {issue.id.upper()}", bold=True)
        click.secho(f"    Severity : {issue.severity.upper()}", **style)
        click.secho(f"    Issue    : {issue.description}")

        if issue.fix_description:
            click.secho(f"    Fix      : {issue.fix_description}", fg="green")

        click.echo()


def run_diagnostics(input_path: Path, fix=False, fixall=False) -> Path:
    """
    Run diagnostics on the dataset at input_path.
    If fix=True: ask user for each fix.
    If fixall=True: apply all fixes automatically.
    Returns path to the fixed dataset.
    """
    click.secho(
        f"\nRunning diagnostics for {(Path(input_path)).name}\n",
        fg="cyan",
        bold=True
    )

    # Detect issues
    issues = run_tabular_diagnostics(input_path)

    if not issues:
        click.secho("✓ No issues detected", fg="green", bold=True)
        return

    display_issues(issues)

    if not fix and not fixall:
        click.secho("End of diagnostics. No fixes applied.", fg="yellow")
        return
    

    input_path = Path(input_path)
    fixed_dir = input_path.parent / "data_fixed"
    fixed_dir.mkdir(exist_ok=True)
    current_file = fixed_dir / input_path.name

    # Copy original dataset first
    shutil.copy(input_path, current_file)


    for i, issue in enumerate(issues, start=1):
        print(f"{i}. [{issue.severity}] {issue.description}")
        if fix or fixall:
            apply = fixall
            if fix and not fixall:
                choice = click.prompt(
                        f"Apply fix for '{issue.id}'",
                        type=click.Choice(["y", "n"]),
                        default="n"
                    )
                apply = choice.lower() == "y"
            if apply:
                # Apply fix
                issue.apply_fix(current_file, current_file)
                click.secho(f"Applied fix: {issue.fix_description}", fg="green")

    click.secho(f"Fixed dataset saved at: {current_file}", fg="green")
    return current_file
