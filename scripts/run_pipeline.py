import subprocess
import sys

SCRIPTS = [
    "scripts/clean_data.py",
    "scripts/build_database.py",
    "scripts/data_quality_report.py"
]


def run_script(script_path):
    print(f"\nRunning: {script_path}")
    result = subprocess.run([sys.executable, script_path], check=False)

    if result.returncode != 0:
        print(f"Error: {script_path} failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    print(f"Completed: {script_path}")


def main():
    print("Starting full pipeline...")

    for script in SCRIPTS:
        run_script(script)

    print("\nPipeline completed successfully!")
    print("Next step: streamlit run app/dashboard.py")


if __name__ == "__main__":
    main()