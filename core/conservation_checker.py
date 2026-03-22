"""
Checks each constraint for conservation violations.
Returns list of check results with pass/fail and delta.
"""

def check_conservation(constraints: list) -> list:
    results = []
    for c in constraints:
        delta  = abs(c["lhs"] - c["rhs"])
        passed = (delta <= c["tolerance"]) and not c["corrupted"]
        results.append({
            "law"     : c["law"],
            "passed"  : passed,
            "delta"   : delta,
            "corrupted": c["corrupted"],
            "detail"  : _describe(c, passed, delta),
        })
    return results

def _describe(c, passed, delta):
    if c["corrupted"]:
        return f"{c['law']}: premise claims impossible state (corruption detected)"
    if not passed:
        return f"{c['law']}: imbalance delta={delta:.4f} exceeds tolerance={c['tolerance']}"
    return f"{c['law']}: balanced within tolerance"
