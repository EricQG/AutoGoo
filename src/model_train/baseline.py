"""
baseline.py — 基线模型训练脚本 (Iris 数据集)

使用 sklearn 经典的分类算法，测量训练时间和推理时间。
作为后续优化的基准 (baseline)。

Standard evaluation metrics for Iris classification:
- Accuracy: 正确分类样本比例 (primary metric)
- Macro F1: 各类别 F1 的未加权平均 (适合均衡数据集)
- Training time: 模型训练耗时
- Inference time: 预测耗时 (per sample)
- Confusion matrix: 各类别混淆情况
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


# ─── Data Loading ──────────────────────────────────────────────────


def load_data(random_state: int = 42) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load Iris dataset and split into train/test sets.

    Returns:
        Tuple of (X_train, X_test, y_train, y_test)
    """
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    return X_train, X_test, y_train, y_test


def preprocess(
    X_train: np.ndarray, X_test: np.ndarray
) -> tuple[np.ndarray, np.ndarray, StandardScaler]:
    """Standardize features by removing mean and scaling to unit variance.

    Returns:
        Tuple of (X_train_scaled, X_test_scaled, scaler)
    """
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    return X_train_scaled, X_test_scaled, scaler


# ─── Baseline Model ────────────────────────────────────────────────


def train_model(
    X_train: np.ndarray, y_train: np.ndarray, n_estimators: int = 100, random_state: int = 42
) -> RandomForestClassifier:
    """Train a Random Forest classifier as baseline.

    Args:
        X_train: Training features
        y_train: Training labels
        n_estimators: Number of trees in the forest
        random_state: Random seed for reproducibility

    Returns:
        Trained RandomForestClassifier
    """
    model = RandomForestClassifier(
        n_estimators=n_estimators,
        random_state=random_state,
        n_jobs=1,  # single-threaded for baseline
    )
    model.fit(X_train, y_train)
    return model


# ─── Evaluation ────────────────────────────────────────────────────


def evaluate_model(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    n_warmup: int = 10,
    n_bench: int = 1000,
) -> dict[str, Any]:
    """Evaluate model and collect all metrics.

    Args:
        model: Trained sklearn model
        X_test: Test features
        y_test: Test labels
        n_warmup: Warmup iterations before timing
        n_bench: Benchmark iterations for timing

    Returns:
        Dictionary of all metrics
    """
    # Prediction quality
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred, target_names=load_iris().target_names, output_dict=True)

    # Inference latency (per-sample)
    # Warmup
    for _ in range(n_warmup):
        _ = model.predict(X_test)

    # Timed runs
    start = time.perf_counter()
    for _ in range(n_bench):
        _ = model.predict(X_test)
    elapsed = time.perf_counter() - start
    inference_time_per_sample = elapsed / (n_bench * len(X_test)) * 1_000  # ms

    return {
        "accuracy": float(accuracy),
        "f1_macro": float(f1_macro),
        "classification_report": report,
        "inference_time_per_sample_ms": inference_time_per_sample,
        "total_inference_time_s": elapsed,
    }


def train_and_evaluate_baseline() -> dict[str, Any]:
    """Full baseline pipeline: load → preprocess → train → evaluate.

    Returns:
        Dictionary with all metrics and model info
    """
    results: dict[str, Any] = {}

    # Load
    load_start = time.perf_counter()
    X_train, X_test, y_train, y_test = load_data()
    results["data_load_time_s"] = time.perf_counter() - load_start
    results["train_shape"] = X_train.shape
    results["test_shape"] = X_test.shape

    # Preprocess
    preprocess_start = time.perf_counter()
    X_train_scaled, X_test_scaled, _ = preprocess(X_train, X_test)
    results["preprocess_time_s"] = time.perf_counter() - preprocess_start

    # Train
    train_start = time.perf_counter()
    model = train_model(X_train_scaled, y_train)
    results["train_time_s"] = time.perf_counter() - train_start
    results["model_params"] = model.get_params()

    # Evaluate
    eval_results = evaluate_model(model, X_test_scaled, y_test)
    results.update(eval_results)

    results["total_time_s"] = (
        results["data_load_time_s"]
        + results["preprocess_time_s"]
        + results["train_time_s"]
        + results["total_inference_time_s"]
    )

    return results


# ─── Main ──────────────────────────────────────────────────────────


def main() -> None:
    print("=" * 60)
    print("Baseline: Iris Classification with Random Forest")
    print("=" * 60)

    results = train_and_evaluate_baseline()

    print(f"\nData: train={results['train_shape']}, test={results['test_shape']}")
    print(f"\n--- Timing ---")
    print(f"  Data load:      {results['data_load_time_s']*1000:.2f} ms")
    print(f"  Preprocess:     {results['preprocess_time_s']*1000:.2f} ms")
    print(f"  Training:       {results['train_time_s']*1000:.2f} ms")
    print(f"  Inference:      {results['total_inference_time_s']*1000:.2f} ms  ({results['inference_time_per_sample_ms']:.4f} ms/sample)")
    print(f"  Total:          {results['total_time_s']*1000:.2f} ms")

    print(f"\n--- Quality ---")
    print(f"  Accuracy:       {results['accuracy']:.4f}")
    print(f"  Macro F1:       {results['f1_macro']:.4f}")

    print(f"\n--- Classification Report ---")
    for cls, metrics in results["classification_report"].items():
        if isinstance(metrics, dict):
            print(f"  {cls:12s}  precision={metrics['precision']:.4f}  recall={metrics['recall']:.4f}  f1={metrics['f1-score']:.4f}")

    return results


if __name__ == "__main__":
    results = main()
