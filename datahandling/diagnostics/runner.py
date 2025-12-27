import shutil
from pathlib import Path
from .tabular import run_tabular_diagnostics

def run_diagnostics(input_path: Path, fix=False, fixall=False) -> Path:
    """
    Run diagnostics on the dataset at input_path.
    If fix=True: ask user for each fix.
    If fixall=True: apply all fixes automatically.
    Returns path to the fixed dataset.
    """
    input_path = Path(input_path)
    fixed_dir = input_path.parent / "data_fixed"
    fixed_dir.mkdir(exist_ok=True)
    current_file = fixed_dir / input_path.name

    # Copy original dataset first
    shutil.copy(input_path, current_file)

    # Detect issues
    issues = run_tabular_diagnostics(current_file)

    if not issues:
        print("No issues detected.")
        return current_file

    print(f"Detected {len(issues)} issue(s).")

    for i, issue in enumerate(issues, start=1):
        print(f"{i}. [{issue.severity}] {issue.description}")
        if fix or fixall:
            apply = fixall
            if fix and not fixall:
                choice = input(f"Do you want to apply fix '{issue.fix_description}'? (y/n): ")
                apply = choice.lower() == "y"
            if apply:
                # Apply fix
                issue.apply_fix(current_file, current_file)
                print(f"Applied fix: {issue.fix_description}")

    print(f"Fixed dataset saved at: {current_file}")
    return current_file
