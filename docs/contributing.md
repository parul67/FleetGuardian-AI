# Contributing to FleetGuardian AI

Thank you for considering a contribution! Please follow these guidelines to keep the codebase consistent and the review process smooth.

---

## Getting Started

1. **Fork** the repository on GitHub.
2. **Clone** your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/FleetGuardian-AI.git
   cd FleetGuardian-AI
   ```
3. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```
4. Follow the [Local Development Setup](../README.md#-local-development-setup) in the README.

---

## Development Workflow

### Backend (Python)

```bash
# Activate the virtual environment
.\venv\Scripts\Activate.ps1   # Windows
source venv/bin/activate       # macOS/Linux

# Install dev dependencies
pip install -r requirements.txt flake8 black

# Run tests before committing
$env:PYTHONPATH="."
pytest tests/ -v

# Lint & format
flake8 app/ --max-line-length=120
black app/ --line-length=120
```

### Frontend (TypeScript/React)

```bash
cd frontend
npm install
npm run lint   # oxlint
npm run build  # Verify it compiles
```

---

## Code Style

### Python
- Follow **PEP 8** with a max line length of **120 characters**.
- Use **type hints** for all function signatures.
- Write docstrings for all public classes and functions.
- Use `black` for formatting and `flake8` for linting.

### TypeScript / React
- Use functional components with hooks.
- Define explicit types for all props and API response shapes.
- Keep components small and focused on a single responsibility.
- Use `oxlint` for linting (already configured via `.oxlintrc.json`).

---

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>

[optional body]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `ci`

Examples:
```
feat(api): add vehicle geofencing endpoint
fix(cv): correct EAR threshold for blink detection
docs(readme): update Docker quick-start instructions
ci(github-actions): add docker build validation job
```

---

## Pull Request Process

1. Ensure all CI checks pass (linting, tests, Docker build).
2. Write or update **tests** for any new functionality.
3. Update **documentation** (`README.md`, `docs/`) if your change affects behaviour.
4. Open a PR against the `main` branch with a clear description of **what** changed and **why**.
5. Address review feedback promptly.

---

## Adding New API Endpoints

1. Create the route handler in `app/api/<resource>.py`.
2. Register it in `app/api/__init__.py`.
3. Add a Pydantic schema in `app/schemas/`.
4. Add a service method in `app/services/`.
5. Write a test in `tests/`.

---

## Reporting Bugs

Use the GitHub Issues template and include:
- Steps to reproduce
- Expected vs. actual behaviour
- Docker / Python / Node version
- Relevant log output (`docker compose logs <service>`)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you agree to uphold this code.
