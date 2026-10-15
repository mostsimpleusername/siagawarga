
# ============================================================
# SIAGAWARGA — EXPLORATORY TEST WITH SURABAYA NER DATASET
# Model: Horizon multilingual zero-shot classification
# Environment: Google Colab
# ===========================================================

import time
import re
import pandas as pd
import torch

from datasets import load_dataset
from transformers import pipeline

# ------------------------------------------------------------
# 1. CONFIGURATION
# ------------------------------------------------------------

DATASET_NAME = "Kiuyha/surabaya-ner-dataset"
MODEL_NAME = "Horizon-Labs/multilingual-zeroshot-small"

TEXT_CANDIDATES = [
    "text",
    "sentence",
    "content",
    "tweet",
    "post",
    "review",
]

LABELS = [
    "a road with a pothole or hole in the road surface",
    "a road with cracked, broken, or peeling asphalt",
    "a road covered by rainwater or floodwater",
    "a fallen tree or branch blocking a road",
    "garbage piled up or scattered along a road",
    "a broken streetlight that does not turn on",
    "a complaint unrelated to these infrastructure problems",
]

LABEL_MAP = {
    LABELS[0]: "jalan berlubang",
    LABELS[1]: "jalan retak atau rusak",
    LABELS[2]: "jalan tergenang banjir",
    LABELS[3]: "pohon tumbang",
    LABELS[4]: "sampah menumpuk di jalan",
    LABELS[5]: "lampu jalan rusak",
    LABELS[6]: "laporan lain atau tidak jelas",
}

KEYWORDS = [
    "jalan", "aspal", "lubang", "berlubang", "retak",
    "rusak", "banjir", "genangan", "tergenang", "air",
    "pohon", "tumbang", "dahan", "sampah", "lampu",
    "penerangan", "infrastruktur", "trotoar", "drainase",
]

MAX_TEXTS = 100
BATCH_SIZE = 8

device = 0 if torch.cuda.is_available() else -1
print("Device:", "GPU" if device == 0 else "CPU")

# ------------------------------------------------------------
# 2. LOAD DATASET
# ------------------------------------------------------------

print("\nLoading dataset...")
ds = load_dataset(DATASET_NAME)

print("\nDataset splits:")
for split_name, split_data in ds.items():
    print(f"{split_name}: {len(split_data)} rows")
    print("Columns:", split_data.column_names)

# ------------------------------------------------------------
# 3. EXTRACT TEXT FROM DIFFERENT POSSIBLE FORMATS
# ------------------------------------------------------------

def find_text_column(column_names):
    for candidate in TEXT_CANDIDATES:
        if candidate in column_names:
            return candidate
    return None


def reconstruct_text(row, text_column):
    # Prefer an existing full-text column
    if text_column is not None:
        value = row.get(text_column)
        if isinstance(value, str) and value.strip():
            return value.strip()

    # Common NER format: list of tokens
    tokens = row.get("tokens")
    if isinstance(tokens, list) and tokens:
        return " ".join(str(token) for token in tokens).strip()

    # Alternative token column names
    for key in ["words", "input_tokens"]:
        value = row.get(key)
        if isinstance(value, list) and value:
            return " ".join(str(token) for token in value).strip()

    return None


records = []

for split_name, split_data in ds.items():
    text_column = find_text_column(split_data.column_names)

    for idx, row in enumerate(split_data):
        text = reconstruct_text(row, text_column)

        if not text:
            continue

        records.append({
            "split": split_name,
            "row_id": idx,
            "text": text,
        })

df = pd.DataFrame(records)

print("\nExtracted text rows:", len(df))

if df.empty:
    raise ValueError(
        "No text could be extracted. Inspect the dataset columns "
        "and adapt reconstruct_text() to its actual schema."
    )

print("\nExample extracted texts:")
for i, text in enumerate(df["text"].head(10), start=1):
    print(f"{i}. {text}")

# ------------------------------------------------------------
# 4. FILTER POSSIBLY RELEVANT TEXTS
# ------------------------------------------------------------

keyword_pattern = re.compile(
    r"\b(?:" + "|".join(map(re.escape, KEYWORDS)) + r")\b",
    flags=re.IGNORECASE,
)

df["possibly_relevant"] = df["text"].apply(
    lambda text: bool(keyword_pattern.search(text))
)

relevant_df = df[df["possibly_relevant"]].copy()

print("\nPotentially relevant rows:", len(relevant_df))

if relevant_df.empty:
    print(
        "No keyword matches found. Dataset may use different vocabulary "
        "or tokenization. Inspect the extracted texts above."
    )
else:
    relevant_df = relevant_df.drop_duplicates(subset=["text"])
    relevant_df = relevant_df.head(MAX_TEXTS).reset_index(drop=True)

    print("Unique texts selected:", len(relevant_df))

# ------------------------------------------------------------
# 5. LOAD ZERO-SHOT MODEL
# ------------------------------------------------------------

print("\nLoading Horizon model...")
load_start = time.time()

classifier = pipeline(
    task="zero-shot-classification",
    model=MODEL_NAME,
    device=device,
)

model_load_seconds = time.time() - load_start
print(f"Model loaded in {model_load_seconds:.2f} seconds")

# ------------------------------------------------------------
# 6. CLASSIFY SELECTED TEXTS
# ------------------------------------------------------------

results = []

if not relevant_df.empty:
    for start in range(0, len(relevant_df), BATCH_SIZE):
        batch = relevant_df.iloc[start:start + BATCH_SIZE]

        for _, row in batch.iterrows():
            text = row["text"]
            infer_start = time.time()

            try:
                output = classifier(
                    text,
                    candidate_labels=LABELS,
                    hypothesis_template="The reported problem is {}.",
                    multi_label=False,
                )

                latency = time.time() - infer_start

                top_label = output["labels"][0]
                top_score = output["scores"][0]

                results.append({
                    "split": row["split"],
                    "row_id": row["row_id"],
                    "text": text,
                    "predicted_category": LABEL_MAP[top_label],
                    "top_score": top_score,
                    "second_label": LABEL_MAP[output["labels"][1]],
                    "second_score": output["scores"][1],
                    "score_margin": top_score - output["scores"][1],
                    "latency_seconds": latency,
                })

            except Exception as exc:
                print(f"\nError on row {row['row_id']}: {exc}")

result_df = pd.DataFrame(results)

# ------------------------------------------------------------
# 7. DISPLAY RESULTS
# ------------------------------------------------------------

if not result_df.empty:
    print("\n" + "=" * 80)
    print("CLASSIFICATION RESULTS")
    print("=" * 80)

    for _, row in result_df.iterrows():
        print("\nREPORT:", row["text"])
        print("PREDICTED:", row["predicted_category"])
        print("TOP SCORE:", round(row["top_score"], 4))
        print("SECOND:", row["second_label"],
              round(row["second_score"], 4))
        print("MARGIN:", round(row["score_margin"], 4))
        print("LATENCY:", round(row["latency_seconds"], 3), "seconds")
        print("-" * 60)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("Total classified:", len(result_df))
    print(
        "Average inference latency:",
        round(result_df["latency_seconds"].mean(), 3),
        "seconds/report",
    )
    print(
        "Median inference latency:",
        round(result_df["latency_seconds"].median(), 3),
        "seconds/report",
    )

    print("\nPredicted category distribution:")
    print(
        result_df["predicted_category"]
        .value_counts()
        .to_string()
    )

    print("\nLowest-score reports for manual review:")
    print(
        result_df.nsmallest(10, "top_score")[
            ["text", "predicted_category", "top_score", "score_margin"]
        ].to_string(index=False)
    )

    # Save for manual review and annotation
    result_df.to_csv(
        "siagawarga_surabaya_exploratory_predictions.csv",
        index=False,
        encoding="utf-8-sig",
    )

    print(
        "\nSaved: siagawarga_surabaya_exploratory_predictions.csv"
    )

else:
    print("\nNo reports were classified.")

# ------------------------------------------------------------
# 8. IMPORTANT EVALUATION NOTES
# ------------------------------------------------------------

print("""
EVALUATION NOTES
----------------
1. These are zero-shot predictions, not validated accuracy.
2. The dataset uses NER labels, not SiagaWarga issue categories.
3. Keyword filtering can miss relevant reports and include irrelevant ones.
4. Scores are relative to the candidate labels; they are not calibrated
   probabilities that a prediction is correct.
5. Review the CSV and manually annotate a representative subset before
   calculating accuracy, precision, recall, or F1.
""")
