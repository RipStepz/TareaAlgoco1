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


MATRIX_ALGO_MAP = {
    "naive": "Naive",
    "strassen": "Strassen",
}

LINE_PATTERN = re.compile(
    r"^\s*([A-Za-z]+)\s*:\s*([0-9eE+\-.]+)\s*ms\s*,\s*(\d+)\s*bytes",
    re.IGNORECASE,
)

ALGORITHM_ORDER = ["Naive", "Strassen"]
N_ORDER = [4, 16, 256, 1024]


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
            algorithm = MATRIX_ALGO_MAP.get(raw_algo.strip().lower(), raw_algo.strip())

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
        return pd.DataFrame(
            columns=[
                "algorithm",
                "n",
                "category",
                "domain",
                "sample",
                "time_ms",
                "memory_bytes",
                "source_file",
            ]
        )

    df = pd.DataFrame([r.__dict__ for r in all_records])
    df["algorithm"] = pd.Categorical(df["algorithm"], categories=ALGORITHM_ORDER, ordered=True)
    return df.sort_values(["category", "domain", "n", "algorithm", "sample"])


def save_line_plot(
    data: pd.DataFrame,
    metric_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    plt.figure(figsize=(10, 6))

    for algorithm in ALGORITHM_ORDER:
        group = data[data["algorithm"] == algorithm].sort_values("n")
        if group.empty:
            continue
        plt.plot(group["n"], group[metric_col], marker="o", linewidth=2, label=algorithm)

    plt.xscale("log", base=2)
    plt.xlabel("n")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def save_bar_plot_for_n(
    subset: pd.DataFrame,
    n_value: int,
    metric_col: str,
    title: str,
    ylabel: str,
    output_path: Path,
) -> None:
    filtered = subset[subset["n"] == n_value].copy()
    if filtered.empty:
        return

    categories = list(filtered["category"].dropna().unique())
    categories.sort()

    x = np.arange(len(categories))
    width = 0.35

    plt.figure(figsize=(10, 6))

    for i, algorithm in enumerate(ALGORITHM_ORDER):
        alg_values = []
        for category in categories:
            cell = filtered[
                (filtered["category"] == category)
                & (filtered["algorithm"] == algorithm)
            ][metric_col]
            alg_values.append(float(cell.iloc[0]) if not cell.empty else 0.0)

        plt.bar(x + (i - 0.5) * width, alg_values, width=width, label=algorithm)

    plt.xticks(x, categories)
    plt.xlabel("Tipo de matriz")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, axis="y", linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()


def generate_matrix_plots(df: pd.DataFrame, output_dir: Path) -> None:
    if df.empty:
        print("[matrix] No se encontraron datos.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    overall = (
        df.groupby(["n", "algorithm"], as_index=False)
        .agg(
            time_ms=("time_ms", "mean"),
            memory_bytes=("memory_bytes", "mean"),
        )
        .sort_values(["n", "algorithm"])
    )

    save_line_plot(
        overall,
        metric_col="time_ms",
        title="Tiempo promedio vs n (todos los casos)",
        ylabel="Tiempo promedio (ms)",
        output_path=output_dir / "matrix_time_general_lineas.png",
    )

    save_line_plot(
        overall,
        metric_col="memory_bytes",
        title="Memoria promedio vs n (todos los casos)",
        ylabel="Memoria promedio (bytes)",
        output_path=output_dir / "matrix_memoria_general_lineas.png",
    )

    by_type = (
        df.groupby(["n", "category", "algorithm"], as_index=False)
        .agg(
            time_ms=("time_ms", "mean"),
            memory_bytes=("memory_bytes", "mean"),
        )
        .sort_values(["n", "category", "algorithm"])
    )

    for n_value in sorted(df["n"].dropna().unique()):
        save_bar_plot_for_n(
            by_type,
            n_value=int(n_value),
            metric_col="time_ms",
            title=f"Tiempo promedio por tipo de matriz (n = {int(n_value)})",
            ylabel="Tiempo promedio (ms)",
            output_path=output_dir / f"matrix_barras_tiempo_n{int(n_value)}.png",
        )

        save_bar_plot_for_n(
            by_type,
            n_value=int(n_value),
            metric_col="memory_bytes",
            title=f"Memoria promedio por tipo de matriz (n = {int(n_value)})",
            ylabel="Memoria promedio (bytes)",
            output_path=output_dir / f"matrix_barras_memoria_n{int(n_value)}.png",
        )

    summary = (
        df.groupby(["n", "category", "domain", "algorithm"], as_index=False)
        .agg(
            avg_time_ms=("time_ms", "mean"),
            avg_memory_bytes=("memory_bytes", "mean"),
            runs=("sample", "count"),
        )
        .sort_values(["n", "category", "domain", "algorithm"])
    )
    summary.to_csv(output_dir / "matrix_summary.csv", index=False)

    print(f"[matrix] Gráficos y resumen guardados en: {output_dir}")


def main() -> None:
    base_dir = Path(__file__).resolve().parent

    matrix_measurements = (base_dir / ".." / "data" / "measurements").resolve()
    matrix_plots = (base_dir / ".." / "data" / "plots").resolve()

    if not matrix_measurements.exists():
        print(f"[matrix] No se encontró carpeta de mediciones: {matrix_measurements}")
        return

    matrix_df = load_records(matrix_measurements)
    generate_matrix_plots(matrix_df, matrix_plots)


if __name__ == "__main__":
    main()
