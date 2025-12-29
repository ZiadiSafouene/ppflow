import shutil
from pathlib import Path
from .tabular import run_tabular_diagnostics
import click
from datahandling.scanner import scan_data
from datahandling.diagnostics.images import run_image_diagnostics

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


from pathlib import Path
import shutil
import click


def run_diagnostics(input_path: Path | None = None, fix=False, fixall=False) -> Path | None:
    """
    Run diagnostics on the dataset.

    If fix=True: ask user for each fix.
    If fixall=True: apply all fixes automatically.
    Returns path to the fixed dataset, or None if no fixes applied.
    """

    click.secho("\nRunning diagnostics...\n", fg="cyan", bold=True)

    # Scan dataset (NO params)
    dataset = scan_data()
    input_root = Path(dataset.root).resolve()

    # ------------------------------
    # Run diagnostics
    # ------------------------------
    if dataset.container_type == "table":
        issues = run_tabular_diagnostics(input_root)
    elif dataset.container_type == "image":
        issues = run_image_diagnostics(input_root)
    else:
        raise ValueError(f"Unsupported container type: {dataset.container_type}")

    if not issues:
        click.secho("✓ No issues detected", fg="green", bold=True)
        return None

    display_issues(issues)

    # Diagnostics-only mode
    if not fix and not fixall:
        click.secho("End of diagnostics. No fixes applied.", fg="yellow")
        return None

    # ------------------------------
    # Prepare FIXED dataset (write-only)
    # ------------------------------
    fixed_root = input_root.parent / f"{input_root.name}_fixed"

    # HARD SAFETY CHECK (prevents your crashes)
    if fixed_root.resolve() == input_root:
        raise RuntimeError("Fixed dataset cannot overwrite input dataset.")

    if fixed_root.exists():
        shutil.rmtree(fixed_root)

    # Copy ONCE
    if input_root.is_file():
        fixed_root.mkdir(parents=True)
        current_path = fixed_root / input_root.name
        shutil.copy2(input_root, current_path)
    else:
        shutil.copytree(input_root, fixed_root)
        current_path = fixed_root

    # ------------------------------
    # Apply fixes (ONLY inside fixed_root)
    # ------------------------------
    for issue in issues:
        apply = fixall

        if fix and not fixall:
            choice = click.prompt(
                f"Apply fix for '{issue.id}'?",
                type=click.Choice(["y", "n"]),
                default="n",
            )
            apply = choice.lower() == "y"

        if apply:
            issue.apply_fix(
                input_path=input_root,     # READ-ONLY
                output_path=current_path   # WRITE-ONLY
            )
            click.secho(f"✔ Applied: {issue.fix_description}", fg="green")

    click.secho(
        f"\nFixed dataset saved at: {current_path}",
        fg="green",
        bold=True,
    )

    return current_path
