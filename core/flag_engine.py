"""
Scores contradiction and returns verdict with full audit trail.
Score 0.0 = clean. Score 1.0 = fully corrupted premise.
"""

def score_and_flag(results: list, parsed: dict = None, constraints: list = None) -> dict:
    total   = len(results)
    failed  = [r for r in results if not r["passed"]]
    score   = len(failed) / total if total else 0.0
    flags   = [r["law"] for r in failed]
    reasons = [r["detail"] for r in failed] or ["No violations detected"]

    if score == 0.0:   verdict = "CLEAN"
    elif score < 0.5:  verdict = "SUSPECT"
    else:              verdict = "CORRUPTED"

    return {
        "verdict"    : verdict,
        "score"      : score,
        "flags"      : flags,
        "reason"     : " | ".join(reasons),
        "details"    : results,
        "audit"      : _build_audit(parsed, constraints, results, verdict, score),
    }

def _build_audit(parsed, constraints, results, verdict, score):
    if not parsed or not constraints:
        return None
    trail = []
    for c, r in zip(constraints, results):
        trail.append({
            "law"          : c["law"],
            "premise_raw"  : parsed.get("raw", ""),
            "claim_type"   : parsed.get("type", "unknown"),
            "direction"    : parsed.get("direction", "unknown"),
            "lhs"          : c["lhs"],
            "rhs"          : c["rhs"],
            "delta"        : abs(c["lhs"] - c["rhs"]),
            "tolerance"    : c["tolerance"],
            "corruption"   : c["corrupted"],
            "passed"       : r["passed"],
            "detail"       : r["detail"],
            "fix_hint"     : _hint(c, r),
        })
    return {
        "verdict"     : verdict,
        "score"       : score,
        "chain"       : trail,
        "summary"     : _summarize(trail),
    }

def _hint(c, r):
    if not r["passed"]:
        if c["corrupted"]:
            return f"Premise claims impossible state under {c['law']} — remove or ground the claim in physical reality"
        delta = abs(c["lhs"] - c["rhs"])
        return f"Balance {c['law']}: lhs={c['lhs']} rhs={c['rhs']} delta={delta:.4f} exceeds tolerance={c['tolerance']}"
    return "No fix required"

def _summarize(trail):
    failed = [t for t in trail if not t["passed"]]
    if not failed:
        return "All constraints satisfied. Premise is physically consistent."
    lines = []
    for t in failed:
        lines.append(
            f"[{t['law']}] FAILED — {t['detail']} | Fix: {t['fix_hint']}"
        )
    return "\n".join(lines)
