from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import matplotlib.pyplot as plt
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


def find_first_existing_dir(candidates: List[Path]) -> Optional[Path]:
    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    return None



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

    return pd.DataFrame([r.__dict__ for r in all_records])



def save_line_plot(
    data: pd.DataFrame,
    x: str,
    y: str,
    hue: str,
    title: str,
    ylabel: str,
    output_path: Path,
    log_x: bool = True,
) -> None:
    plt.figure(figsize=(10, 6))

    for label, group in data.groupby(hue):
        group = group.sort_values(x)
        plt.plot(group[x], group[y], marker="o", linewidth=2, label=label)

    if log_x:
        plt.xscale("log", base=10)

    plt.xlabel("n")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()



def save_grouped_plots_by_category(
    df: pd.DataFrame,
    output_dir: Path,
    metric_col: str,
    metric_label: str,
    prefix: str,
    category_field: str,
    category_title: str,
) -> None:
    for category in sorted(df[category_field].dropna().unique()):
        subset = df[df[category_field] == category]
        grouped = (
            subset.groupby(["n", "algorithm"], as_index=False)[metric_col]
            .mean()
            .sort_values(["algorithm", "n"])
        )
        save_line_plot(
            grouped,
            x="n",
            y=metric_col,
            hue="algorithm",
            title=f"{metric_label} promedio vs n ({category_title}: {category})",
            ylabel=metric_label,
            output_path=output_dir / f"{prefix}_{category}.png",
        )



def save_case_count_plot(df: pd.DataFrame, output_path: Path) -> None:
    counts = df.groupby(["n", "algorithm"], as_index=False).size()

    plt.figure(figsize=(10, 6))
    for label, group in counts.groupby("algorithm"):
        group = group.sort_values("n")
        plt.plot(group["n"], group["size"], marker="o", linewidth=2, label=label)

    plt.xscale("log", base=10)
    plt.xlabel("n")
    plt.ylabel("Cantidad de mediciones")
    plt.title("Cobertura de mediciones por n (sorting)")
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()



def generate_sorting_plots(df: pd.DataFrame, output_dir: Path) -> None:
    if df.empty:
        print("[sorting] No se encontraron datos.")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    avg_time = df.groupby(["n", "algorithm"], as_index=False)["time_ms"].mean()
    save_line_plot(
        avg_time,
        x="n",
        y="time_ms",
        hue="algorithm",
        title="Tiempo promedio de ejecución vs n (todos los casos)",
        ylabel="Tiempo promedio (ms)",
        output_path=output_dir / "sorting_time_avg_overall.png",
    )

    avg_mem = df.groupby(["n", "algorithm"], as_index=False)["memory_bytes"].mean()
    save_line_plot(
        avg_mem,
        x="n",
        y="memory_bytes",
        hue="algorithm",
        title="Memoria promedio vs n (todos los casos)",
        ylabel="Memoria promedio (bytes)",
        output_path=output_dir / "sorting_memory_avg_overall.png",
    )

    save_grouped_plots_by_category(
        df,
        output_dir,
        metric_col="time_ms",
        metric_label="Tiempo promedio (ms)",
        prefix="sorting_time_by_type",
        category_field="category",
        category_title="tipo",
    )

    save_grouped_plots_by_category(
        df,
        output_dir,
        metric_col="memory_bytes",
        metric_label="Memoria promedio (bytes)",
        prefix="sorting_memory_by_type",
        category_field="category",
        category_title="tipo",
    )

    save_grouped_plots_by_category(
        df,
        output_dir,
        metric_col="time_ms",
        metric_label="Tiempo promedio (ms)",
        prefix="sorting_time_by_domain",
        category_field="domain",
        category_title="dominio",
    )

    save_grouped_plots_by_category(
        df,
        output_dir,
        metric_col="memory_bytes",
        metric_label="Memoria promedio (bytes)",
        prefix="sorting_memory_by_domain",
        category_field="domain",
        category_title="dominio",
    )

    save_case_count_plot(df, output_dir / "sorting_case_count.png")

    summary = (
        df.groupby(["n", "category", "domain", "algorithm"], as_index=False)
        .agg(
            avg_time_ms=("time_ms", "mean"),
            avg_memory_bytes=("memory_bytes", "mean"),
            runs=("sample", "count"),
        )
        .sort_values(["n", "category", "domain", "algorithm"])
    )
    summary.to_csv(output_dir / "sorting_summary.csv", index=False)
    print(f"[sorting] Gráficos y resumen guardados en: {output_dir}")



def main() -> None:
    base_dir = Path(__file__).resolve().parent

    sorting_measurements = sorting_measurements = (base_dir / ".." / "data" / "measurements").resolve()
    sorting_plots = base_dir / ".." / "data" / "plots"

    if sorting_measurements is None:
        print("[sorting] No se encontró carpeta de mediciones de sorting.")
        return

    sorting_df = load_records(sorting_measurements)
    generate_sorting_plots(sorting_df, sorting_plots)


if __name__ == "__main__":
    main()
