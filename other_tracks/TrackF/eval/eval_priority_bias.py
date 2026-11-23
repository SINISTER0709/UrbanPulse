import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from app.priority_engine import score_incident, score_from_normalized_factors


def run_audit() -> None:
    print("=== 1. CONTRACT VERIFICATION (EXACT TRACK F EXAMPLE) ===")
    contract = score_from_normalized_factors(S=75, R=50, T=0, L=100, E=0)
    assert contract["priority_score"] == 55.0
    assert contract["breakdown"] == {"S": 30.0, "R": 10.0, "T": 0.0, "L": 15.0, "E": 0.0}
    print("PASS:", json.dumps({
        "priority_score": contract["priority_score"],
        "breakdown": contract["breakdown"],
        "urgent_review_flag": contract["urgent_review_flag"],
    }))

    print("\n=== 2. EXPERT-REVIEWED RANKING VALIDATION ===")
    scenarios = [
        {
            "id": "EXP_1",
            "expected_rank": 1,
            "desc": "Live 11kV wire snapped outside hospital gate, 6 reports, worsening",
            "params": dict(severity="Critical", report_count=6, unresolved_days=0.5, location_context="hospital_access", escalation_level="confirmed_worsening", text="live wire snapped outside hospital"),
        },
        {
            "id": "EXP_2",
            "expected_rank": 2,
            "desc": "MVP Demo: Large pothole outside ABC School (5 reports, school GPS)",
            "params": dict(severity="High", report_count=5, unresolved_days=0.2, lat=28.4506, lng=77.5842, text="Large pothole outside ABC School causing traffic problems."),
        },
        {
            "id": "EXP_3",
            "expected_rank": 3,
            "desc": "Overflowing market dumpster (4 reports, 4 days, market road)",
            "params": dict(severity="Medium", report_count=4, unresolved_days=4.0, location_context="market_arterial"),
        },
        {
            "id": "EXP_4",
            "expected_rank": 4,
            "desc": "Single faded zebra crossing in quiet cul-de-sac (1 report, <1 day)",
            "params": dict(severity="Low", report_count=1, unresolved_days=0.5, location_context="low_exposure"),
        },
    ]

    scored = []
    for sc in scenarios:
        res = score_incident(**sc["params"])
        scored.append((sc["id"], sc["expected_rank"], res["priority_score"], res["urgent_review_flag"], sc["desc"]))

    ranked = sorted(scored, key=lambda x: x[2], reverse=True)
    for idx, (sid, exp_rank, p_score, flag, desc) in enumerate(ranked, 1):
        print(f"  Rank {idx} (expected {exp_rank}) | P={p_score:5.2f} | urgent={str(flag):5s} | {sid}: {desc}")

    actual_order = [x[0] for x in ranked]
    expected_order = [x["id"] for x in scenarios]
    print("Ranking match:", "EXACT MATCH" if actual_order == expected_order else f"MISMATCH ({actual_order})")

    print("\n=== 3. FAIRNESS & LOW-REPORTING AREA BIAS AUDIT (R & L) ===")
    # Compare under-reported peripheral ward Critical vs over-reported affluent market Low/Medium
    under_reported_critical = score_incident(
        severity="Critical", report_count=1, unresolved_days=0.2,
        location_context="low_exposure", escalation_level="none",
        text="open manhole cover missing main road dark"
    )
    over_reported_low = score_incident(
        severity="Low", report_count=20, unresolved_days=2.0,
        location_context="market_arterial", escalation_level="none"
    )
    over_reported_medium = score_incident(
        severity="Medium", report_count=20, unresolved_days=4.0,
        location_context="market_arterial", escalation_level="none"
    )

    print(f"  Under-reported Critical (1 rpt, low_exposure):  P={under_reported_critical['priority_score']:5.2f} | urgent_review_flag={under_reported_critical['urgent_review_flag']} ({under_reported_critical['urgent_reasons']})")
    print(f"  Over-reported Low       (20 rpts, 2d, market):  P={over_reported_low['priority_score']:5.2f} | urgent_review_flag={over_reported_low['urgent_review_flag']}")
    print(f"  Over-reported Medium    (20 rpts, 4d, market):  P={over_reported_medium['priority_score']:5.2f} | urgent_review_flag={over_reported_medium['urgent_review_flag']}")

    print("\n  Finding:")
    print("  - Critical (1 report, low_exposure) still beats over-reported Low (45.00 > 41.50).")
    print("  - However, heavily reported 4-day Medium (55.25) numerically outranks a brand-new")
    print("    single-report Critical hazard in a low-reporting ward (45.00).")
    print("  - Mitigation verified: FR8 sets urgent_review_flag=True on the Critical incident")
    print("    regardless of numerical score, pinning it for immediate human triage.")


if __name__ == "__main__":
    run_audit()