# Source Coverage

This page describes the current local source configuration.
It does not certify that every adapter has successfully collected data.

| Repository | Configured mode | Enabled | Notes |
|---|---|---|---|
| `cyanseek/VibeMath` | `vibemath_feed` | Yes | Inspect the deployed adapter for actual Feed support. |
| `bonninr/awesome-ai-solved-math` | `readme_index` | Yes | Coverage depends on the active adapter and source format. |
| `MColbrook/AIM` | `aim_resolved` | Yes | AIM status and result scope require source-specific interpretation. |
| `openai/math` | `issues` | No | A manuscript catalogue is not automatically a solved-problem catalogue. |

## Important Limitations

- An enabled source can produce zero imported records.
- The source adapter may index only a subset of the repository.
- Counts of claims do not equal counts of distinct solved problems.
- OMP does not verify mathematics or scientific priority.

See [Methodology](../METHODOLOGY.md).
