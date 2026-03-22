"""
PhysicsGuard v1 — Physics-grounded logic verification
Detects corrupted premises via thermodynamic constraint checking
CC0 — github.com/JinnZ2/physicsguard
"""

import sys

from core.conservation_checker import check_conservation
from core.constraint_mapper import map_to_constraints
from core.flag_engine import score_and_flag
from core.premise_parser import parse_premise


def run(premise: str) -> dict:
    parsed     = parse_premise(premise)
    constraints = map_to_constraints(parsed)
    result     = check_conservation(constraints)
    verdict    = score_and_flag(result, parsed, constraints)
    return verdict

if __name__ == "__main__":
    premise = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Premise: ")
    v = run(premise)
    print("\n[PhysicsGuard v1]")
    print(f"Verdict       : {v['verdict']}")
    print(f"Contradiction : {v['score']:.3f}")
    print(f"Flags         : {v['flags']}")
    print(f"Reason        : {v['reason']}")
