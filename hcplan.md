# Hill Climbing Deadlock Solutions - Implementation Plan

## Current Problem
The `HillClimbingSolver` gets stuck in local maxima during Phase 2 optimization, resulting in:
- 1 unresolved conflict
- 1 detected deadlock (incomplete path or mutual blockage)

## Root Cause
The `hill_climb()` method (lines 357-397) only accepts **strictly better** neighbors. When all candidate replans preserve the same conflict count but can't improve, it converges prematurely at `no_imp > 200`.

---

## Implementation Plan

### 1. Simulated Annealing Integration
**Location**: `HillClimbingSolver` class, add to `__init__` and `hill_climb()`

- Add parameters: `temperature`, `cooling_rate`
- Modify acceptance criteria to allow worse moves with probability `exp(-delta/T)`
- Start with high T (accept many bad moves), cool down over iterations
- This escapes local maxima by accepting temporary "downhill" moves

### 2. Random Restarts with Best-So-Far Memory
**Location**: `HillClimbingSolver.hill_climb()`

- Track global best paths (lowest conflicts, then shortest length)
- After early convergence (`no_imp > 200`), restart from shuffled priorities
- Keep best solution across all restarts, not just current run
- Limit total restarts to prevent infinite loops

### 3. Plateau / Sideways Move Handler
**Location**: Within `hill_climb()` acceptance logic

- When `new_conf == current_conflicts` but length is equal (plateau):
  - Allow a small random chance to accept anyway (diversification)
- Or: try random robot sequence permutations on plateaus

### 4. Conflict-Focused Neighborhood Selection
**Location**: `HillClimbingSolver.hill_climb()`

- Instead of random robot selection, bias toward robots involved in conflicts
- The conflict report already identifies which robots are conflicting
- Prioritize replanning those first (may break the local maximum faster)

### 5. Enhanced Deadlock Detection + Recovery
**Location**: New method in `HillClimbingSolver` or separate function

- Detect stuck robots early (not reaching goal at end of path)
- Force replan of stuck robots with higher priority
- Use wider reservation window to unblock them

---

## Files to Modify
- `HC.ipynb` - all changes go here (cells 4, 5, and add new evaluation cell)

## Verification
After implementation, re-run the 20-robot evaluation:
- Expect: 0 conflicts, 0 deadlocks
- Runtime may increase but should still complete < 5 minutes
