"""Generate evidence plots from an Arctos experiment CSV."""

import argparse
import csv
from pathlib import Path


def _read_float_rows(csv_path: Path) -> list[dict[str, float]]:
    with csv_path.open(newline='') as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, float]] = []
        for row in reader:
            rows.append({key: float(value) for key, value in row.items()})
    if not rows:
        raise ValueError(f'No rows found in {csv_path}')
    return rows


def generate_plots(csv_path: str | Path) -> list[Path]:
    """Generate raw-vs-compensated and improvement plots next to a CSV."""
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    csv_path = Path(csv_path).expanduser().resolve()
    rows = _read_float_rows(csv_path)
    sample_index = list(range(1, len(rows) + 1))
    raw_error = [row['raw_error'] for row in rows]
    compensated_error = [row['compensated_error'] for row in rows]
    improvement = [row['improvement_percent'] for row in rows]

    raw_plot = csv_path.parent / 'raw_vs_compensated.png'
    improvement_plot = csv_path.parent / 'improvement_over_time.png'

    plt.figure(figsize=(9, 5))
    plt.plot(sample_index, raw_error, label='Raw target error', linewidth=2)
    plt.plot(sample_index, compensated_error, label='Compensated target error', linewidth=2)
    plt.title('Raw vs Compensated Target Error')
    plt.xlabel('Sample')
    plt.ylabel('Error magnitude')
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(raw_plot, dpi=160)
    plt.close()

    plt.figure(figsize=(9, 5))
    plt.plot(sample_index, improvement, label='Improvement percent', color='tab:green', linewidth=2)
    plt.axhline(0.0, color='black', linestyle='--', linewidth=1, label='No improvement')
    plt.title('Compensation Improvement Over Time')
    plt.xlabel('Sample')
    plt.ylabel('Improvement (%)')
    plt.grid(True, alpha=0.35)
    plt.legend()
    plt.tight_layout()
    plt.savefig(improvement_plot, dpi=160)
    plt.close()

    return [raw_plot, improvement_plot]


def main(args=None):
    parser = argparse.ArgumentParser(description='Generate Arctos experiment plots from a CSV file.')
    parser.add_argument('csv_path', help='Path to an experiment results CSV')
    parsed = parser.parse_args(args=args)
    for path in generate_plots(parsed.csv_path):
        print(path)


if __name__ == '__main__':
    main()
