"""Statistical analysis for Arctos calibration compensation experiments."""

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean, median, stdev


def _read_rows(csv_path: Path) -> list[dict[str, float]]:
    with csv_path.open(newline='') as f:
        reader = csv.DictReader(f)
        rows = [{key: float(value) for key, value in row.items()} for row in reader]
    if not rows:
        raise ValueError(f'No experiment rows found in {csv_path}')
    return rows


def _confidence_interval_95(values: list[float]) -> tuple[float, float]:
    if len(values) < 2:
        value = values[0]
        return value, value
    center = mean(values)
    standard_error = stdev(values) / math.sqrt(len(values))
    margin = 1.96 * standard_error
    return center - margin, center + margin


def _summary(rows: list[dict[str, float]]) -> dict[str, float | int | list[float]]:
    raw_errors = [row['raw_error'] for row in rows]
    compensated_errors = [row['compensated_error'] for row in rows]
    improvements = [row['improvement_percent'] for row in rows]
    ci_low, ci_high = _confidence_interval_95(improvements)

    return {
        'sample_count': len(rows),
        'mean_raw_error': mean(raw_errors),
        'mean_compensated_error': mean(compensated_errors),
        'mean_improvement_percent': mean(improvements),
        'median_improvement_percent': median(improvements),
        'std_improvement_percent': stdev(improvements) if len(improvements) > 1 else 0.0,
        'min_improvement_percent': min(improvements),
        'max_improvement_percent': max(improvements),
        'confidence_interval_95': [ci_low, ci_high],
    }


def _generate_plots(output_dir: Path, improvements: list[float]) -> list[Path]:
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    histogram_path = output_dir / 'histogram_improvement.png'
    boxplot_path = output_dir / 'boxplot_improvement.png'

    plt.figure(figsize=(9, 5))
    plt.hist(improvements, bins='auto', color='tab:blue', edgecolor='black', alpha=0.8)
    plt.title('Distribution of Compensation Improvement')
    plt.xlabel('Improvement (%)')
    plt.ylabel('Sample count')
    plt.grid(True, alpha=0.35)
    plt.tight_layout()
    plt.savefig(histogram_path, dpi=160)
    plt.close()

    plt.figure(figsize=(7, 5))
    plt.boxplot(improvements, labels=['Improvement'], showmeans=True)
    plt.title('Compensation Improvement Boxplot')
    plt.ylabel('Improvement (%)')
    plt.grid(True, axis='y', alpha=0.35)
    plt.tight_layout()
    plt.savefig(boxplot_path, dpi=160)
    plt.close()

    return [boxplot_path, histogram_path]


def analyze(csv_path: str | Path) -> tuple[dict[str, float | int | list[float]], list[Path]]:
    csv_path = Path(csv_path).expanduser().resolve()
    rows = _read_rows(csv_path)
    summary = _summary(rows)
    output_dir = csv_path.parent

    summary_path = output_dir / 'experiment_summary.json'
    with summary_path.open('w') as f:
        json.dump(summary, f, indent=2)
        f.write('\n')

    improvements = [row['improvement_percent'] for row in rows]
    plot_paths = _generate_plots(output_dir, improvements)
    return summary, [summary_path, *plot_paths]


def _print_summary(summary: dict[str, float | int | list[float]]):
    ci_low, ci_high = summary['confidence_interval_95']
    print('Experiment Summary')
    print(f"Sample Count: {summary['sample_count']}")
    print(f"Mean Raw Error: {summary['mean_raw_error']:.6f}")
    print(f"Mean Compensated Error: {summary['mean_compensated_error']:.6f}")
    print(f"Mean Improvement: {summary['mean_improvement_percent']:.6f}%")
    print(f"Median Improvement: {summary['median_improvement_percent']:.6f}%")
    print(f"Std Improvement: {summary['std_improvement_percent']:.6f}%")
    print(f"95% CI: [{ci_low:.6f}%, {ci_high:.6f}%]")
    print(f"Min Improvement: {summary['min_improvement_percent']:.6f}%")
    print(f"Max Improvement: {summary['max_improvement_percent']:.6f}%")


def main(args=None):
    parser = argparse.ArgumentParser(
        description='Analyze Arctos calibration compensation experiment results.'
    )
    parser.add_argument('csv_path', help='Path to experiment results CSV')
    parsed = parser.parse_args(args=args)

    summary, output_paths = analyze(parsed.csv_path)
    _print_summary(summary)
    for path in output_paths:
        print(path)


if __name__ == '__main__':
    main()
