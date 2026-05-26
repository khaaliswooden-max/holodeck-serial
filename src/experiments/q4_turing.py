"""Q4 -- Is T=4 {move, create, destroy, query} a Turing-complete vocabulary?

Open question (docs/open_questions.md, Q4): is the MVW interaction vocabulary
computationally universal? It blocks EG-01's "arbitrary environment" claim.

Argument (constructive): a Minsky register machine with instructions INC(r),
DEC(r), and JZ(r, L) (jump if register r is zero) over >= 2 unbounded registers
is Turing-complete (Minsky, 1967). These map EXACTLY onto a subset of T against
an MVW world, where register r is the population of entity-type r:

    register r value  :=  number of entities with type == r   (via QUERY)
    INC(r)            :=  CREATE an entity of type r
    DEC(r)            :=  QUERY for an entity of type r, then DESTROY it
    JZ(r, L)          :=  QUERY the type-r population; branch if zero

So {create, destroy, query} alone is Turing-complete; `move` adds spatial
expressiveness, not computational power (T=4 is sufficient; T=3 already suffices).

IMPORTANT caveat (stated honestly): Turing-completeness is a property of the
instruction set PLUS a control layer that branches on observations. The
primitives supply the universal operations; the branching (JZ/JMP + program
counter) is the control layer, exactly as an ISA needs a program counter. A
fixed, straight-line event log is NOT universal; the vocabulary driven by
query-conditioned control IS.

This script proves the reduction empirically: it stores ALL machine state in an
MVW world using only create/destroy/query, then executes real INC/DEC/JZ
programs (addition, multiplication) and checks the results against native
arithmetic.

    python src/experiments/q4_turing.py
"""

import json
import os
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))
_CORE = os.path.join(_HERE, "..", "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from world import World, TYPE                  # noqa: E402
from observer import Observer                  # noqa: E402

_RESULTS = os.path.join(_HERE, "..", "..", "results")


class WorldRegisterMachine:
    """A register machine whose registers ARE entity-type populations in an MVW
    world, manipulated ONLY through the T primitives create / destroy / query.

    The interpreter loop (PC, JZ/JMP) is the control layer; every data
    operation goes through the world's interaction vocabulary."""

    def __init__(self, max_steps=2_000_000):
        self.world = World(bounds=100.0)
        self.observer = Observer(self.world)     # Phi: the query endpoint
        self.max_steps = max_steps
        self.prim_counts = {"create": 0, "destroy": 0, "query": 0}

    # --- the only state access is via these three T primitives ---

    def _count(self, r):
        """QUERY: population of entity-type r (reads full state via the
        observer, then counts)."""
        self.prim_counts["query"] += 1
        return sum(1 for e in self.observer.snapshot() if e["type"] == r)

    def inc(self, r):
        """CREATE an entity of type r."""
        self.prim_counts["create"] += 1
        self.world.create(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, r)

    def dec(self, r):
        """QUERY for a type-r entity, then DESTROY it (no-op if none)."""
        self.prim_counts["query"] += 1
        for e in self.world.entities:
            if e[TYPE] == r:
                self.prim_counts["destroy"] += 1
                self.world.destroy(e[0])
                return True
        return False

    # --- load initial register values (via CREATE) ---

    def load(self, regs):
        for r, val in regs.items():
            for _ in range(val):
                self.inc(r)

    def read(self, r):
        return self._count(r)

    # --- execute an INC/DEC/JZ/JMP/HALT program ---

    def run(self, program):
        pc = 0
        steps = 0
        while pc < len(program):
            if steps > self.max_steps:
                raise RuntimeError("step budget exceeded (non-halting?)")
            steps += 1
            ins = program[pc]
            op = ins[0]
            if op == "inc":
                self.inc(ins[1]); pc += 1
            elif op == "dec":
                self.dec(ins[1]); pc += 1
            elif op == "jz":
                pc = ins[2] if self._count(ins[1]) == 0 else pc + 1
            elif op == "jmp":
                pc = ins[1]
            elif op == "halt":
                break
            else:
                raise ValueError("bad opcode %r" % (op,))
        return steps


# --- programs written purely in the register-machine instruction set ---

# R0 := R0 + R1  (consumes R1).
ADD = [
    ("jz", 1, 4),   # 0: if R1==0 -> halt
    ("dec", 1),     # 1
    ("inc", 0),     # 2
    ("jmp", 0),     # 3
    ("halt",),      # 4
]

# R2 := R0 * R1  (consumes R0; preserves R1 using temp R3).
MUL = [
    ("jz", 0, 12),  # 0: while R0>0
    ("dec", 0),     # 1
    ("jz", 1, 7),   # 2: inner copy: while R1>0 -> R2,R3
    ("dec", 1),     # 3
    ("inc", 2),     # 4
    ("inc", 3),     # 5
    ("jmp", 2),     # 6
    ("jz", 3, 11),  # 7: restore: while R3>0 -> R1
    ("dec", 3),     # 8
    ("inc", 1),     # 9
    ("jmp", 7),     # 10
    ("jmp", 0),     # 11
    ("halt",),      # 12
]


def main():
    print("Q4: is T={move,create,destroy,query} Turing-complete?")
    print("=" * 60)
    print("Reduction: register machine over entity-type populations,")
    print("driven ONLY by create / destroy / query.\n")

    checks = []

    # Addition battery
    print("ADD  (R0 += R1, via create/destroy/query):")
    for a, b in [(0, 0), (1, 0), (0, 5), (3, 4), (7, 9), (12, 20)]:
        m = WorldRegisterMachine()
        m.load({0: a, 1: b})
        m.run(ADD)
        got = m.read(0)
        ok = got == a + b
        checks.append(ok)
        print("   %2d + %2d = %2d  %s" % (a, b, got, "OK" if ok else "FAIL"))

    # Multiplication battery (nested loops -> genuine control flow)
    print("MUL  (R2 = R0 * R1, nested loops, temp register):")
    for a, b in [(0, 7), (1, 1), (3, 4), (5, 6), (9, 9), (12, 11)]:
        m = WorldRegisterMachine()
        m.load({0: a, 1: b})
        m.run(MUL)
        got = m.read(2)
        r1_preserved = m.read(1) == b
        ok = (got == a * b) and r1_preserved
        checks.append(ok)
        print("   %2d * %2d = %3d  (R1 preserved=%s)  %s"
              % (a, b, got, r1_preserved, "OK" if ok else "FAIL"))

    # Report primitive usage for one representative run.
    m = WorldRegisterMachine()
    m.load({0: 9, 1: 9})
    m.run(MUL)
    all_ok = all(checks)
    print("=" * 60)
    print("primitive calls for 9*9: %s" % m.prim_counts)
    verdict = (
        "T is Turing-complete: {create, destroy, query} implement a Minsky "
        "register machine (Turing-complete with >=2 unbounded registers + "
        "query-conditioned branching). All %d ADD/MUL programs ran correctly "
        "using only the interaction vocabulary as storage. `move` is not needed "
        "for universality. Caveat: branching lives in the control layer (PC + "
        "JZ), as with any instruction set." % len(checks)
        if all_ok else "FAILURE: some programs returned wrong results.")
    print("VERDICT:", verdict)

    report = {
        "experiment": "Q4 Turing completeness",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "reduction": "Minsky register machine; register r = type-r population; "
                     "INC=create, DEC=query+destroy, JZ=query-zero",
        "all_programs_correct": all_ok,
        "n_checks": len(checks),
        "primitive_calls_9x9": m.prim_counts,
        "minimal_subset": ["create", "destroy", "query"],
        "move_required_for_universality": False,
        "caveat": "Turing-completeness requires query-conditioned control flow "
                  "(PC + JZ); the primitives supply the universal operations.",
        "verdict": verdict,
    }
    os.makedirs(_RESULTS, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = os.path.join(_RESULTS, "q4_turing_%s.json" % stamp)
    with open(path, "w") as fh:
        json.dump(report, fh, indent=2)
    print("wrote %s" % os.path.relpath(path, os.path.join(_HERE, "..", "..")))
    return report


if __name__ == "__main__":
    main()
