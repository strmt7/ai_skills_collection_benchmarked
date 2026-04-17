# Curated Skill Stack

This repository uses one project skill plus a small set of responsibilities.

## Responsibility split

1. Workflow and context discipline
   - Durable instructions
   - Exact failure framing
   - Screenshot and log-backed verification
2. Game and simulation
   - Missile and interceptor math
   - Radar and layout contracts
   - Shared GUI and headless simulation behavior
3. Graphics and compatibility
   - Lighting, materials, effects, textures, and mobile-safe rendering
4. UI ergonomics
   - Button size, hierarchy, adaptive layout, and state feedback
5. Measurement and QA
   - Performance proof
   - Automated and emulator verification

## Non-overlap rules

- Workflow guidance should not redefine gameplay math.
- Graphics changes must not silently rewrite simulation behavior.
- Performance claims need measurements, not intuition.
- QA confirms behavior; it does not invent target behavior.
