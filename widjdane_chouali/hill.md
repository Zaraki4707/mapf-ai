# Hill Climbing Fix Plan

## Current Problems

1. Only 1 iteration runs - algorithm stops immediately
2. Score function doesn't measure real improvement
3. No conflict resolution - conflicts stay same before/after (71→71)
4. Missing proper Hill Climbing objective function

## Solution Plan

### Phase 1: Fix Core Hill Climbing Logic

1. **Proper Objective Function**
   - Weighted sum: `α * conflicts + β * makespan + γ * flowtime`
   - Must actually decrease to trigger iteration

2. **Neighbor Generation**
   - Generate multiple random neighbors from current solution
   - Apply random path modifications (detours, swaps, replanning)
   - Accept best neighbor that improves score

3. **Main Loop**
   - Loop until max_iterations or no improvement found
   - Track best solution found

### Phase 2: Conflict Resolution Strategies

1. **Priority-based Replanning**
   - Identify robots with most conflicts
   - Replan their paths using A* with conflict avoidance

2. **Temporal Offset**
   - Add wait times at specific timesteps to avoid vertex conflicts

3. **Path Exchange**
   - Try swapping path segments between conflicting robots

### Phase 3: Testing & Validation

1. Run with 20+ agents on grid.txt
2. Verify conflicts decrease (71 → 0)
3. Measure iteration count and runtime
4. Compare makespan before/after

## Implementation Order

1. Rewrite `optimize()` method with proper neighbor generation
2. Add `generate_neighbors()` function
3. Add `replan_path()` for conflict-heavy robots
4. Test and verify conflict reduction

## Expected Outcome

- Multiple iterations (>10)
- Conflicts reduced significantly
- Still maintains validity (start/end positions unchanged)