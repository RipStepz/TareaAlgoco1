# plot_generator_final.py

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


@dataclass
class Record:
    algorithm: str
    n: int
    category: str
    domain: str
    sample: str
    time_ms: float
    memory_bytes: int
    source_file: str


SORTING_ALGO_MAP = {
    "mergesort": "MergeSort",
    "quicksort": "QuickSort",
    "sort": "Sort",
    "stdsort": "Sort",
}

LINE_PATTERN = re.compile(
    r"^\s*([A-Za-z]+)\s*:\s*([0-9eE+\-.]+)\s*ms\s*,\s*(\d+)\s*bytes",
    re.IGNORECASE,
)

ALGORITHM_ORDER = ["MergeSort", "QuickSort", "Sort"]
N_ORDER = [10, 1000, 100000]


def parse_measurement_file(file_path: Path) -> List[Record]:
    stem_parts = file_path.stem.split("_")
    if len(stem_parts) < 4:
        return []

    try:
        n = int(stem_parts[0])
    except ValueError:
        return []

    category, domain, sample = stem_parts[1], stem_parts[2], stem_parts[3]

    records: List[Record] = []
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            match = LINE_PATTERN.search(line)
            if not match:
                continue

            raw_algo, time_ms, memory_bytes = match.groups()
            algorithm = SORTING_ALGO_MAP.get(raw_algo.strip().lower(), raw_algo.strip())

            records.append(
                Record(
                    algorithm=algorithm,
                    n=n,
                    category=category,
                    domain=domain,
                    sample=sample,
                    time_ms=float(time_ms),
                    memory_bytes=int(memory_bytes),
                    source_file=file_path.name,
                )
            )
    return records


def load_records(measurements_dir: Path) -> pd.DataFrame:
    all_records: List[Record] = []
    for file_path in sorted(measurements_dir.glob("*.txt")):
        all_records.extend(parse_measurement_file(file_path))

    if not all_records:
        return pd.DataFrame()

    return pd.DataFrame([r.__dict__ for r in all_records])


def save_line_plot(data, metric_col, title, ylabel, output_path):
    plt.figure(figsize=(10, 6))

    for algo in ALGORITHM_ORDER:
        subset = data[data["algorithm"] == algo].sort_values("n")
        if subset.empty:
            continue
        plt.plot(subset["n"], subset[metric_col], marker="o", label=algo)

    plt.xscale("log", base=10)
    plt.xlabel("n")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_bar_plot_for_n(data, n_value, metric_col, title, ylabel, output_path):
    subset = data[data["n"] == n_value]
    if subset.empty:
        return

    categories = sorted(subset["category"].unique())
    x = np.arange(len(categories))
    width = 0.25

    plt.figure(figsize=(10, 6))

    for i, algo in enumerate(ALGORITHM_ORDER):
        values = []
        for cat in categories:
            v = subset[(subset["category"] == cat) & (subset["algorithm"] == algo)][metric_col]
            values.append(float(v.iloc[0]) if not v.empty else 0)

        plt.bar(x + (i - 1) * width, values, width=width, label=algo)

    plt.xticks(x, categories)
    plt.xlabel("Tipo")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend()
    plt.grid(axis="y")
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def generate_sorting_plots(df: pd.DataFrame, output_dir: Path):
    if df.empty:
        print("No hay datos")
        return

    overall = df.groupby(["n", "algorithm"], as_index=False).agg(
        time_ms=("time_ms", "mean"),
        memory_bytes=("memory_bytes", "mean"),
    )

    save_line_plot(
        overall,
        "time_ms",
        "Tiempo promedio vs n",
        "Tiempo (ms)",
        output_dir / "time_general.png",
    )

    save_line_plot(
        overall,
        "memory_bytes",
        "Memoria promedio vs n",
        "Memoria (bytes)",
        output_dir / "memory_general.png",
    )

    by_type = df.groupby(["n", "category", "algorithm"], as_index=False).agg(
        time_ms=("time_ms", "mean"),
        memory_bytes=("memory_bytes", "mean"),
    )

    for n in N_ORDER:
        save_bar_plot_for_n(
            by_type,
            n,
            "time_ms",
            f"Tiempo por tipo (n={n})",
            "Tiempo (ms)",
            output_dir / f"time_n{n}.png",
        )

        save_bar_plot_for_n(
            by_type,
            n,
            "memory_bytes",
            f"Memoria por tipo (n={n})",
            "Memoria (bytes)",
            output_dir / f"memory_n{n}.png",
        )


def main():
    base_dir = Path(__file__).resolve().parent

    measurements = (base_dir / ".." / "data" / "measurements").resolve()
    plots = (base_dir / ".." / "data" / "plots").resolve()

    df = load_records(measurements)
    generate_sorting_plots(df, plots)


if __name__ == "__main__":
    main()
