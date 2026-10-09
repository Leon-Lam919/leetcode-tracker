# What each build step teaches

| # | Step | Skill it shows |
|---|---|---|
| 1 | Scaffold | Project layout, pinned dependencies, keeping secrets out of git with `.gitignore` |
| 2 | Config, DB, models, health | Typed settings with `pydantic-settings`, fail-fast config checks, SQLModel tables, FastAPI dependencies |
| 3 | Streaks | Pure functions and table-style unit tests for tricky date logic |
| 4 | Solve CRUD, stats, heatmap | REST design (status codes 201/204/404/409), routers vs. services, test isolation with a temp DB |
| 5 | LeetCode client and sync | Wrapping an unofficial API in one module, retries and timeouts, idempotency, mocking HTTP with `respx` |
| 6 | Frontend core | React state with `useState`/`useEffect`, a small custom hook, `fetch` wrappers, testing components with mocked `fetch` |
| 7 | Heatmap, stats, filters | CSS grid layout, responsive design at 375px, dark mode with Tailwind `dark:` classes |
| 8 | Docker | Dockerfiles, multi-stage builds, nginx as a reverse proxy, Compose healthchecks and volumes |
| 9 | CI | GitHub Actions jobs that lint, test, and build on every push and pull request |
| 10 | README and LEARNING | Writing docs a stranger can follow: setup, run, test, and architecture |
