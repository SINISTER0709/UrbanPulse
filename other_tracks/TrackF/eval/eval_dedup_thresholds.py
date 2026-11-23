import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.location_risk import load_config


def evaluate_thresholds(model_name: str, csv_path: Path, max_dist_m: float, window_days: int) -> None:
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} labeled pairs from {csv_path}")
    print(f"Encoding with {model_name} ...")

    model = SentenceTransformer(model_name)
    emb_a = model.encode(df["text_a"].tolist(), normalize_embeddings=True, show_progress_bar=False)
    emb_b = model.encode(df["text_b"].tolist(), normalize_embeddings=True, show_progress_bar=False)
    df["cosine_sim"] = np.sum(emb_a * emb_b, axis=1)

    # Spatial + category + temporal pre-filter gate (FR5)
    gate_pass = (
        (df["category_a"] == df["category_b"])
        & (df["distance_m"] <= max_dist_m)
        & (df["time_diff_days"] <= window_days)
    )

    y_true = df["is_duplicate"].values
    thresholds = [0.50, 0.55, 0.60, 0.65, 0.68, 0.70, 0.72, 0.75, 0.78, 0.80, 0.85]

    print(f"\n=== THRESHOLD SWEEP (radius <= {max_dist_m}m, window <= {window_days}d, same category) ===")
    print(f"{'Thresh':>6} | {'Prec':>6} | {'Recall':>6} | {'F1':>6} | {'FP':>3} | {'FN':>3} | {'False-Merge Rate (FPR)':>22}")
    print("-" * 74)

    sweep_rows = []
    best = None

    for th in thresholds:
        y_pred = (gate_pass & (df["cosine_sim"] >= th)).astype(int).values
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0  # False-merge rate over non-duplicates

        row = {
            "threshold": th,
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1": round(float(f1), 4),
            "tp": int(tp),
            "fp": int(fp),
            "fn": int(fn),
            "tn": int(tn),
            "false_merge_rate": round(float(fpr), 4),
        }
        sweep_rows.append(row)
        print(f"{th:6.2f} | {prec:6.4f} | {rec:6.4f} | {f1:6.4f} | {fp:3d} | {fn:3d} | {fpr*100:21.2f}%")

        # Prefer highest F1; break ties by lower false-merge rate
        if best is None or (f1 > best["f1"]) or (f1 == best["f1"] and fpr < best["false_merge_rate"]):
            best = row

    print("\n=== BEST OPERATING THRESHOLD ===")
    print(json.dumps(best, indent=2))

    # Error analysis at best threshold
    best_th = best["threshold"]
    df["pred"] = (gate_pass & (df["cosine_sim"] >= best_th)).astype(int)
    errors_df = df[df["pred"] != df["is_duplicate"]]

    print(f"\n=== ERROR ANALYSIS ({len(errors_df)} mistakes at sim >= {best_th:.2f}) ===")
    error_list = []
    for _, r in errors_df.iterrows():
        err_kind = "FALSE_MERGE (FP)" if r["pred"] == 1 else "MISSED_DUP (FN)"
        item = {
            "pair_id": r["pair_id"],
            "error_type": err_kind,
            "pair_type": r["pair_type"],
            "cosine_sim": round(float(r["cosine_sim"]), 4),
            "distance_m": float(r["distance_m"]),
            "time_diff_days": float(r["time_diff_days"]),
            "text_a": r["text_a"],
            "text_b": r["text_b"],
        }
        error_list.append(item)
        print(f"  [{r['pair_id']} | {err_kind} | {r['pair_type']}] sim={r['cosine_sim']:.3f} dist={r['distance_m']}m")
        print(f"    A: {r['text_a']}")
        print(f"    B: {r['text_b']}")

    # High-confidence tier check (zero false-merge target for upper band)
    zero_fp_thresholds = [r for r in sweep_rows if r["fp"] == 0]
    recommended_auto = zero_fp_thresholds[0]["threshold"] if zero_fp_thresholds else 0.90

    out = {
        "model": model_name,
        "max_distance_meters": max_dist_m,
        "time_window_days": window_days,
        "num_pairs": len(df),
        "best_review_threshold": best,
        "recommended_high_confidence_threshold": recommended_auto,
        "sweep": sweep_rows,
        "errors": error_list,
    }
    out_path = Path("eval/eval_dedup_results.json")
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nSaved full evaluation report to {out_path}")
    print(f"Tip: Update config.json -> admin_review_similarity={best_th}, auto_link_similarity={max(recommended_auto, best_th + 0.15):.2f}")


if __name__ == "__main__":
    cfg = load_config()["deduplication"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=cfg["embedding_model"])
    parser.add_argument("--csv", default="data/duplicate_pairs_labeled.csv")
    parser.add_argument("--dist", type=float, default=cfg["max_distance_meters"])
    parser.add_argument("--days", type=int, default=cfg["time_window_days"])
    args = parser.parse_args()
    evaluate_thresholds(args.model, Path(args.csv), args.dist, args.days)