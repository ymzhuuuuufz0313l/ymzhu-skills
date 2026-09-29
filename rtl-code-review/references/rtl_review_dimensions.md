# RTL Review Dimensions

## 0. Retiming / tap-move consumer audit（重定时消费者审计）
Trigger: the diff moves any signal's effective beat — new pipeline register, load source
switched to a delayed version (`_D`), comparator/judge input moved to a different tap,
output now driven by a pipelined version.

Checks:
- Enumerate ALL consumers (cross-module) of every moved signal. For each, answer:
  "which beat does this consumer assume the signal arrives on?" Produce a
  before/after beat-difference table.
- Hunt three killer structures:
  1. **Same-beat cross-tap comparators**: judges/masks placing two differently-delayed
     signals into one expression (anti-retrigger masks, key-rotation judges). The mask
     window lag is a **calibrated behavior parameter**, not an implementation detail —
     it must not move with the implementation.
  2. **Load-window == first-action-window cascade**: every extra delay stage in the
     select/enable chain must be matched by an equal delay in the data reference chain.
  3. **Level state machines**: verify decision VALUE and decision EDGE pairing
     separately; retiming can preserve one and break the other.
- Equivalence evidence: static "relative geometry preserved" reasoning is **NOT
  acceptable** as pass evidence (data/state-dependent acceptance sets are invisible to
  static analysis — real-stream period structure can make a lag change behaviorally
  material). Require an **old-vs-new same-stimulus differential simulation** (iverilog
  suffices): drive both versions identically, compare key event sequences
  (detect/load/find). A uniform +N beat shift is acceptable; ANY shape difference
  (extra/missing pulses, different values, different acceptance beats) is a defect —
  locate the first divergence event.
- Severity: a consumer whose before/after beat difference changed without an invariance
  argument = **CRITICAL**.

## 1. Correctness
- Logic matches specification
- Edge cases handled (reset, overflow, underflow)
- State machines have valid transitions
- No combinational loops

## 2. Safety
- No unintended latches
- All signals assigned in all branches
- Reset covers all registers
- Clock domain crossings properly synchronized

## 3. Traceability
- @requirement annotations present
- @spec_hash matches current spec
- REQ_ID references valid and unique
- Module header matches MAS definition

## 4. Performance
- Critical path minimization
- No unnecessary pipeline stages
- Resource sharing where appropriate
- Power gating opportunities identified

## 5. Style
- Naming follows coding style guide
- Consistent formatting
- No dead code
- Comments explain non-obvious decisions
