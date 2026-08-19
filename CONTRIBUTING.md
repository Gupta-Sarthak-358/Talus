# Contributing

Talus is built by a six-person team over a short hackathon timeline. These rules keep us from stepping on each other's toes.

## Branches

```text
main
dev
feature/<name>
```

Examples:

```text
feature/risk-engine
feature/dashboard
feature/routing
```

Working flow:

```text
                         main
                          │
                          ▼
                         dev
            ┌─────────────┼──────────────┐
            │             │              │
            ▼             ▼              ▼
      feature/ml    feature/backend   feature/frontend
            │             │              │
            └─────────────┼──────────────┘
                          ▼
                         dev
                          │
                          ▼
                        main
```

## Rules

1. **Never push directly to `main`.**
2. One feature per branch.
3. Pull the latest `dev` before starting work.
4. Test before opening a PR.
5. Keep commits focused.
6. Update documentation when the API or schema changes.

## Commit Style

Use conventional prefixes:

```text
feat: add risk prediction endpoint
fix: correct risk band mapping
docs: update data provenance
refactor: simplify route engine
chore: update dependencies
```

## Documentation Rules

- The docs under `docs/` are the **single source of truth**. If you change behavior, update the matching doc in the same PR.
- If you add or change an API endpoint, update `docs/05_API_SPEC.md`.
- If you introduce a new data source or feature, update the provenance table in `docs/03_DATA_PLAN.md`.
- Never commit large datasets or trained model weights. See `.gitignore`.

## Large Data / Models

- Small sample data can be committed. Real datasets live outside git (LFS, Drive, Hugging Face).
- Trained models are stored separately from code. Metadata travels in the repo; weights do not.