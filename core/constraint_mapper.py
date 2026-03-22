"""
Translates parsed premise into physical constraint equations.
Each constraint is a dict: {law, lhs, rhs, tolerance}
"""

def map_to_constraints(parsed: dict) -> list:
    constraints = []
    t = parsed["type"]

    if t == "thermodynamic":
        constraints.append(_first_law(parsed))
        constraints.append(_second_law(parsed))
    elif t == "mass_balance":
        constraints.append(_mass_conservation(parsed))
    else:
        constraints.append(_generic_balance(parsed))

    return constraints

def _first_law(p):
    # dU = Q - W  (energy in = energy out + work done)
    # If premise claims creation from nothing, lhs != rhs
    mag = sum(p["magnitude"])
    direction_factor = 1 if p["direction"] == "positive" else -1
    return {
        "law"       : "first_law_thermodynamics",
        "lhs"       : mag * direction_factor,
        "rhs"       : mag * direction_factor,
        "corrupted" : "create" in p["keywords"] and "destroy" not in p["keywords"],
        "tolerance" : 0.01,
    }

def _second_law(p):
    # Entropy of isolated system never decreases
    # Premise claiming perpetual extraction with no entropy cost = corrupted
    extraction_claim = any(k in p["keywords"] for k in ["extract","produce","generate"])
    negated_kw = p.get("negated_kw", [])
    entropy_keywords = ["heat","entropy","temperature"]
    entropy_mentioned = any(k in p["keywords"] for k in entropy_keywords)
    entropy_negated = any(k in negated_kw for k in entropy_keywords)
    # Entropy is only truly accounted for if mentioned AND not negated
    entropy_cost = entropy_mentioned and not entropy_negated
    corrupted = extraction_claim and not entropy_cost
    # Only create imbalance when there's an extraction claim
    lhs = 1 if extraction_claim else 0
    rhs = 1 if (extraction_claim and entropy_cost) else 0
    return {
        "law"       : "second_law_thermodynamics",
        "lhs"       : lhs,
        "rhs"       : rhs,
        "corrupted" : corrupted,
        "tolerance" : 0.0,
    }

def _mass_conservation(p):
    mag = sum(p["magnitude"])
    return {
        "law"       : "mass_conservation",
        "lhs"       : mag,
        "rhs"       : mag,
        "corrupted" : p["negations"] > 1,
        "tolerance" : 0.01,
    }

def _generic_balance(p):
    return {
        "law"       : "generic_balance",
        "lhs"       : 1.0,
        "rhs"       : 1.0,
        "corrupted" : p["negations"] > 2,
        "tolerance" : 0.1,
    }
