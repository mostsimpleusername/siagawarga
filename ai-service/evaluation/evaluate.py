#!/usr/bin/env python3
"""
Offline evaluation script for SiagaWarga CLIP image classifier.
Evaluates accuracy and performance against annotated ground truth samples in samples.csv.
"""

import argparse
import csv
import os
import sys
import time
from collections import defaultdict
from PIL import Image

# Add parent directory to path so 'app' is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.classifier import CLIPClassifier


def evaluate(csv_path: str, base_dir: str = None) -> None:
    if not os.path.exists(csv_path):
        print(f"Error: Evaluation file '{csv_path}' not found.")
        sys.exit(1)

    if base_dir is None:
        base_dir = os.path.dirname(csv_path)

    print(f"Loading classifier for evaluation...")
    classifier = CLIPClassifier()

    total_samples = 0
    correct_samples = 0
    evaluated_samples = 0
    per_class_counts = defaultdict(lambda: {"total": 0, "correct": 0})
    latencies = []

    print(f"\nEvaluating dataset: {csv_path}\n" + "-" * 60)

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sample_id = row.get("sample_id", "")
            image_rel_path = row.get("image_path", "")
            expected_category = row.get("expected_category", "").strip()

            image_full_path = os.path.join(base_dir, image_rel_path)
            total_samples += 1

            if not os.path.exists(image_full_path):
                print(f"[SKIP] Sample #{sample_id}: Image not found at '{image_full_path}'")
                continue

            try:
                with Image.open(image_full_path) as img:
                    img_rgb = img.convert("RGB")

                start_t = time.time()
                result = classifier.classify(img_rgb)
                elapsed_ms = (time.time() - start_t) * 1000
                latencies.append(elapsed_ms)

                predicted_category = result["predicted_category"]["category_id"]
                score = result["predicted_category"]["score"]

                evaluated_samples += 1
                per_class_counts[expected_category]["total"] += 1

                is_correct = predicted_category == expected_category
                if is_correct:
                    correct_samples += 1
                    per_class_counts[expected_category]["correct"] += 1
                    status_str = "PASS"
                else:
                    status_str = f"FAIL (got '{predicted_category}')"

                print(
                    f"Sample #{sample_id:>2} | Expected: {expected_category:<18} | "
                    f"Score: {score:.4f} | {status_str:<22} | {elapsed_ms:5.1f}ms"
                )

            except Exception as e:
                print(f"[ERROR] Sample #{sample_id} ({image_rel_path}): {e}")

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total entries in CSV: {total_samples}")
    print(f"Images evaluated:    {evaluated_samples}")

    if evaluated_samples > 0:
        overall_acc = (correct_samples / evaluated_samples) * 100
        avg_latency = sum(latencies) / len(latencies)
        print(f"Overall Accuracy:    {overall_acc:.2f}% ({correct_samples}/{evaluated_samples})")
        print(f"Avg Inference Latency: {avg_latency:.1f}ms per image")
        print("\nPer-Category Recall:")
        for cat, stats in sorted(per_class_counts.items()):
            tot = stats["total"]
            corr = stats["correct"]
            recall = (corr / tot * 100) if tot > 0 else 0.0
            print(f"  - {cat:<20}: {recall:5.1f}% ({corr}/{tot})")
    else:
        print("No image files could be evaluated. Place test images in the evaluation directory to run benchmark.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate SiagaWarga CLIP classifier")
    parser.add_argument(
        "--csv",
        default=os.path.join(os.path.dirname(__file__), "samples.csv"),
        help="Path to samples.csv",
    )
    parser.add_argument(
        "--base-dir",
        default=None,
        help="Base directory containing sample images (defaults to CSV directory)",
    )
    args = parser.parse_args()
    evaluate(args.csv, args.base_dir)
