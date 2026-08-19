# routing

Risk-aware routing for Talus.

Risk-weighted Dijkstra over the mine road graph:
`cost(edge) = length(edge) × (1 + α × max(risk of adjacent zones))`

See `docs/02_ARCHITECTURE.md` and `docs/05_API_SPEC.md`.