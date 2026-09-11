import json
import random
from pathlib import Path
from typing import List, Dict, Any

def validate_record(record: Dict[str, Any]) -> bool:
    required_keys = ["id", "category", "incoming_email", "reference_reply"]
    for key in required_keys:
        if key not in record:
            return False
        val = record[key]
        if not isinstance(val, str) or not val.strip():
            return False
    return True

def prepare_dataset(
    raw_path: str = "data/raw/emails.json",
    processed_dir: str = "data/processed",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Dict[str, int]:
    random.seed(seed)
    
    raw_file = Path(raw_path)
    if not raw_file.exists():
        raise FileNotFoundError(f"Raw dataset file not found at {raw_path}")

    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Validate & remove empty
    valid_records = []
    for record in data:
        if validate_record(record):
            valid_records.append(record)

    # 2. Remove exact duplicates
    seen_pairs = set()
    unique_records = []
    for record in valid_records:
        pair_key = (record["incoming_email"].strip(), record["reference_reply"].strip())
        if pair_key not in seen_pairs:
            seen_pairs.add(pair_key)
            unique_records.append(record)

    # 3. Shuffle with fixed seed for reproducibility
    random.shuffle(unique_records)

    total_count = len(unique_records)
    train_end = int(total_count * train_ratio)
    val_end = train_end + int(total_count * val_ratio)

    train_data = unique_records[:train_end]
    val_data = unique_records[train_end:val_end]
    test_data = unique_records[val_end:]

    out_dir = Path(processed_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "train.json", "w", encoding="utf-8") as f:
        json.dump(train_data, f, indent=2, ensure_ascii=False)

    with open(out_dir / "validation.json", "w", encoding="utf-8") as f:
        json.dump(val_data, f, indent=2, ensure_ascii=False)

    with open(out_dir / "test.json", "w", encoding="utf-8") as f:
        json.dump(test_data, f, indent=2, ensure_ascii=False)

    counts = {
        "raw_total": len(data),
        "cleaned_total": total_count,
        "train": len(train_data),
        "validation": len(val_data),
        "test": len(test_data)
    }

    print(f"Dataset preparation complete:")
    print(f"  Raw records: {counts['raw_total']}")
    print(f"  Cleaned & Unique: {counts['cleaned_total']}")
    print(f"  Train split (70%): {counts['train']}")
    print(f"  Validation split (15%): {counts['validation']}")
    print(f"  Test split (15%): {counts['test']}")

    return counts

if __name__ == "__main__":
    prepare_dataset()
