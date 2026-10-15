import time
from transformers import pipeline

MODEL_NAME = "Horizon-Labs/multilingual-zeroshot-small"

# Label bahasa Inggris untuk model.

LABEL_MAP = {
    "a road surface with a clear hole or pothole":
        "jalan berlubang",

    "cracked, broken, or peeling asphalt without a clear hole":
        "jalan retak atau rusak",

    "rainwater or floodwater covering the road surface":
        "jalan tergenang banjir",

    "a fallen tree or fallen branch blocking or endangering the road":
        "pohon tumbang",

    "a pile of garbage or scattered waste along the roadside":
        "sampah menumpuk di jalan",

    "a broken streetlight or a streetlight that does not turn on":
        "lampu jalan rusak",

    "a public complaint unrelated to the road, flooding, trees, garbage, or streetlights":
        "laporan lain atau tidak jelas",
}

CANDIDATE_LABELS = list(LABEL_MAP.keys())

REPORTS = [
    ("Ada lubang besar di depan sekolah, motor hampir jatuh.",
     "jalan berlubang"),
    ("Aspal jalan retak memanjang dan mulai mengelupas.",
     "jalan retak atau rusak"),
    ("Air hujan menggenangi jalan sehingga kendaraan sulit lewat.",
     "jalan tergenang banjir"),
    ("Pohon besar tumbang dan menutup akses jalan.",
     "pohon tumbang"),
    ("Sampah rumah tangga menumpuk di pinggir jalan.",
     "sampah menumpuk di jalan"),
    ("Lampu penerangan jalan rusak sejak beberapa hari lalu.",
     "lampu jalan rusak"),
    ("Mohon segera ditindaklanjuti masalah di lingkungan kami.",
     "laporan lain atau tidak jelas"),
    ("Lubang jalan di depan puskesmas sangat dalam.", "jalan berlubang"),
    ("Ban motor saya hampir masuk ke lubang di aspal.", "jalan berlubang"),
    ("Banyak lubang kecil tersebar sepanjang jalan desa.", "jalan berlubang"),

    ("Permukaan aspal pecah dan retak di beberapa bagian.", "jalan retak atau rusak"),
    ("Aspal jalan mengelupas dan permukaannya tidak rata.", "jalan retak atau rusak"),

    ("Hujan deras membuat air menutupi jalan utama.", "jalan tergenang banjir"),
    ("Kendaraan tidak bisa lewat karena jalan tergenang air.", "jalan tergenang banjir"),

    ("Pohon kelapa roboh dan melintang di jalan.", "pohon tumbang"),
    ("Dahan pohon besar jatuh dan menghalangi akses warga.", "pohon tumbang"),

    ("Sampah plastik dan sisa makanan berserakan di pinggir jalan.", "sampah menumpuk di jalan"),
    ("Tumpukan sampah belum diangkut selama beberapa hari.", "sampah menumpuk di jalan"),

    ("Lampu jalan mati sehingga kawasan gelap pada malam hari.", "lampu jalan rusak"),
    ("Tiang penerangan jalan masih berdiri, tetapi lampunya tidak menyala.", "lampu jalan rusak"),

    ("Permisi, saya ingin menyampaikan keluhan tentang pelayanan kantor desa.", "laporan lain atau tidak jelas"),
]





CANDIDATE_LABELS = list(LABEL_MAP.keys())

print("Loading Horizon model...")
load_start = time.perf_counter()

classifier = pipeline(
    "zero-shot-classification",
    model=MODEL_NAME,
    device=-1,
)
GROUP_LABELS = [
    "damage to a road surface, such as potholes or cracked asphalt",
    "environmental obstruction, such as a fallen tree or accumulated garbage",
    "broken or nonfunctioning public infrastructure, such as streetlights",
    "floodwater covering or blocking a road",
    "a complaint unrelated to these public infrastructure problems",
]


TEST_CASES = [
    {
        "text": "Ada lubang besar di tengah jalan yang membahayakan pengendara.",
        "expected": "jalan berlubang",
    },
    {
        "text": "Aspal jalan retak memanjang, tetapi tidak ada lubang.",
        "expected": "jalan retak atau rusak",
    },
    {
        "text": "Permukaan aspal mengelupas dan bergelombang tanpa lubang.",
        "expected": "jalan retak atau rusak",
    },
    {
        "text": "Air hujan menggenangi jalan hingga setengah roda motor.",
        "expected": "jalan tergenang banjir",
    },
    {
        "text": "Pohon tumbang melintang dan menutup seluruh badan jalan.",
        "expected": "pohon tumbang",
    },
    {
        "text": "Lampu jalan mati sehingga jalan gelap pada malam hari.",
        "expected": "lampu jalan rusak",
    },
]


GROUP_TESTS = [
    {
        "text": "Pohon kelapa roboh dan melintang di jalan.",
        "expected_group": GROUP_LABELS[1],
    },
    {
        "text": "Aspal jalan retak memanjang dan mulai mengelupas.",
        "expected_group": GROUP_LABELS[0],
    },
    {
        "text": "Kendaraan tidak bisa lewat karena jalan tergenang air.",
        "expected_group": GROUP_LABELS[3],
    },
    {
        "text": "Mohon segera ditindaklanjuti masalah di lingkungan kami.",
        "expected_group": GROUP_LABELS[4],
    },
    {
        "text": "Lampu jalan mati sehingga kawasan gelap pada malam hari.",
        "expected_group": GROUP_LABELS[2],
    },
]


# Tahap 1: kelompok masalah
GROUP_TO_CATEGORIES = {
    "damage to a road surface, such as potholes or cracked asphalt": [
        "a road surface with a clear hole or pothole",
        "cracked, broken, or peeling asphalt without a clear hole",
    ],
    "environmental obstruction, such as a fallen tree or accumulated garbage": [
        "a fallen tree or fallen branch blocking or endangering the road",
        "a pile of garbage or scattered waste along the roadside",
    ],
    "broken or nonfunctioning public infrastructure, such as streetlights": [
        "a broken streetlight or a streetlight that does not turn on",
    ],
    "floodwater covering or blocking a road": [
        "rainwater or floodwater covering the road surface",
    ],
    "a complaint unrelated to these public infrastructure problems": [
        "a public complaint unrelated to the listed infrastructure problems",
    ],
}

CATEGORY_TO_LABEL = {
    "a road surface with a clear hole or pothole":
        "jalan berlubang",
    "cracked, broken, or peeling asphalt without a clear hole":
        "jalan retak atau rusak",
    "a fallen tree or fallen branch blocking or endangering the road":
        "pohon tumbang",
    "a pile of garbage or scattered waste along the roadside":
        "sampah menumpuk di jalan",
    "a broken streetlight or a streetlight that does not turn on":
        "lampu jalan rusak",
    "rainwater or floodwater covering the road surface":
        "jalan tergenang banjir",
    "a public complaint unrelated to the listed infrastructure problems":
        "laporan lain atau tidak jelas",
}

HYPOTHESIS = "The reported problem is {}."

def classify_hierarchical(text):
    # Tahap 1
    group_result = classifier(
        text,
        candidate_labels=list(GROUP_TO_CATEGORIES.keys()),
        hypothesis_template=HYPOTHESIS,
        multi_label=False,
    )

    selected_group = group_result["labels"][0]
    category_candidates = GROUP_TO_CATEGORIES[selected_group]

    # Tahap 2
    category_result = classifier(
        text,
        candidate_labels=category_candidates,
        hypothesis_template=HYPOTHESIS,
        multi_label=False,
    )

    selected_category = category_result["labels"][0]

    return {
        "group": selected_group,
        "category": CATEGORY_TO_LABEL[selected_category],
        "group_score": group_result["scores"][0],
        "category_score": category_result["scores"][0],
    }


for case in GROUP_TESTS:
    result = classifier(
        case["text"],
        candidate_labels=GROUP_LABELS,
        hypothesis_template="The reported problem is {}.",
        multi_label=False,
    )

    predicted = result["labels"][0]

    print("REPORT   :", case["text"])
    print("EXPECTED :", case["expected_group"])
    print("PREDICTED:", predicted)
    print("CORRECT  :", predicted == case["expected_group"])
    print("SCORE    :", round(result["scores"][0], 4))
    print("-" * 60)

print(f"Model ready in {time.perf_counter() - load_start:.2f}s")

correct = 0
total_latency = 0.0

for report, expected in REPORTS:
    start = time.perf_counter()

    result = classifier(
        report,
        candidate_labels=CANDIDATE_LABELS,
        hypothesis_template="The reported problem is {}.",
        multi_label=False,
    )

    elapsed = time.perf_counter() - start
    total_latency += elapsed

    predicted = LABEL_MAP[result["labels"][0]]
    is_correct = predicted == expected
    correct += int(is_correct)

    print("\n" + "=" * 60)
    print("REPORT:", report)
    print("EXPECTED:", expected)
    print("PREDICTED:", predicted)
    print("CORRECT:", is_correct)
    print("TOP SCORE:", round(result["scores"][0], 4))
    print("LATENCY:", round(elapsed, 3), "seconds")

    for label, score in zip(result["labels"], result["scores"]):
        print(f"  {LABEL_MAP[label]}: {score:.4f}")


for case in TEST_CASES:
    result = classify_hierarchical(case["text"])

    print("REPORT          :", case["text"])
    print("EXPECTED        :", case["expected"])
    print("PREDICTED       :", result["category"])
    print("CORRECT         :", result["category"] == case["expected"])
    print("GROUP SCORE     :", round(result["group_score"], 4))
    print("CATEGORY SCORE  :", round(result["category_score"], 4))
    print("-" * 60)



print("\n" + "=" * 60)
print(f"CORRECT: {correct}/{len(REPORTS)}")
print(f"SMOKE TEST ACCURACY: {correct / len(REPORTS):.2%}")
print(f"AVERAGE LATENCY: {total_latency / len(REPORTS):.3f}s")
