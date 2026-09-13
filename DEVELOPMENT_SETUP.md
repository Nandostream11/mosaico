# Development Setup Guide for Mosaico

This guide walks you through setting up the Mosaico repository for local development and contributing code.

## ✅ Prerequisites Installed

The following have been automatically installed on your system:

- **Rust 1.98.1** - Rust compiler and Cargo package manager
  - Located at: `~/.cargo/bin`
- **Poetry 2.4.3** - Python dependency manager
  - Located at: `~/.local/bin`
- **Python 3.12.3** - Meets requirement of Python 3.10+
- **Docker & Docker Compose** - For infrastructure (database, etc.)
- **Git pre-commit hooks** - Installed for automatic code quality checks

## 📁 Repository Structure

This is a monorepo containing three main components:

### 1. **Python SDK** (`mosaico-sdk-py/`)
The primary Python interface for interacting with Mosaico.
- **Key files**: `pyproject.toml`, `src/mosaicolabs/`, `src/mosaicolabs_cli/`
- **Package manager**: Poetry
- **Python version**: 3.10+
- **Status**: ✅ Dependencies installed at `mosaico-sdk-py/.venv/`

### 2. **Rust Daemon** (`mosaicod/`)
The backend server that handles data processing and storage.
- **Key files**: `Cargo.toml` (workspace), `crates/*/`
- **Package manager**: Cargo
- **Rust version**: 1.92+ (you have 1.98.1)
- **Build setup**: Ready for compilation

### 3. **Documentation** (`docs/`)
Project documentation split into two parts:
- `docs/main/` - Main documentation (Next.js/Docusaurus)
- `docs/py/` - Python SDK documentation

## 🛠️ Development Commands

### Python SDK Development

```bash
cd mosaico-sdk-py

# Enter the Poetry environment
poetry shell

# Or run commands with Poetry
poetry run python -c "import mosaicolabs; print(mosaicolabs.__version__)"

# Run tests
poetry run pytest

# Code quality checks (Ruff)
poetry run ruff check --fix src/
poetry run ruff format src/

# Install dependencies (if needed)
poetry install
```

### Rust Daemon Development

```bash
cd mosaicod

# Check for compilation errors (without building)
export SQLX_OFFLINE=true
cargo check

# Build the binary
cargo build

# Build with optimizations (release)
cargo build --release

# Run tests
cargo test

# Code quality checks (Clippy)
cargo clippy --all-targets

# Format code
cargo fmt

# Run the dev environment script (includes database setup)
bash ../scripts/dev_env
```

### Documentation

```bash
# Main documentation
cd docs/main
npm install
npm run dev

# Python SDK documentation
cd docs/py
pip install -r requirements.txt  # or use Poetry
mkdocs serve
```

## 🔄 Pre-commit Hooks

Git pre-commit hooks are automatically installed and will run code quality checks before each commit.

**Configured checks**:
- Python: Ruff linting + formatting (`mosaico-sdk-py`)
- Rust: Clippy + rustfmt (configured in `clippy.toml` and `rustfmt.toml`)

To bypass pre-commit checks (use sparingly):
```bash
git commit --no-verify
```

## 🐳 Setting Up the Development Environment

For local testing with a full Mosaico stack (database + daemon):

```bash
# Start PostgreSQL database for development
cd docker/testing
docker compose up -d

# In another terminal, run the development environment script
cd /path/to/mosaico
export SQLX_OFFLINE=true
bash scripts/dev_env

# This will:
# - Start the mosaicod daemon
# - Connect to the test database
# - Configure the storage backend
```

**Environment variables used**:
- `DATABASE_URL`: PostgreSQL connection string
- `RUST_LOG`: Logging level (set to `mosaico=trace` by default)
- `SQLX_OFFLINE`: Set to `true` (avoids needing live database for compilation)
- `MOSAICOD_STORE_ENDPOINT`: File storage endpoint
- `MOSAICOD_STORE_BUCKET`: Storage bucket name

## 📝 Before Making Contributions

1. **Read the Contribution Guidelines**
   - See [CONTRIBUTING.md](./CONTRIBUTING.md)
   - Only approved contributors can submit PRs
   - Reach out to `foss@mosaico.dev` to become approved

2. **Follow Git Workflow**
   - Create a topic branch: `git checkout -b feature/your-feature-name`
   - Commit with conventional commit messages
   - Push and create a Pull Request

3. **Code Quality**
   - Pre-commit hooks will run automatically
   - Ensure all tests pass locally
   - Fix any linting/formatting issues before pushing

4. **Commit Message Format**
   - Use Conventional Commits: `type(scope): description`
   - See [release cycle documentation](https://docs.mosaico.dev/dev/release_cycle)

## 🔗 Useful Resources

- **Main Documentation**: https://docs.mosaico.dev
- **Python SDK Docs**: https://docs.mosaico.dev/python-sdk/
- **Daemon Docs**: https://docs.mosaico.dev/daemon/
- **GitHub Issues**: Report bugs via Discussions (see CONTRIBUTING.md)
- **Discord**: https://discord.gg/mwQtFnsckE

## 📦 Key Dependencies

### Python
- `pyarrow` (Arrow data format)
- `pandas` (Data manipulation)
- `pydantic` (Data validation)
- `rosbags` (ROS bag support)
- `pytest` (Testing)
- `ruff` (Linting & formatting)

### Rust
- `arrow`, `parquet`, `datafusion` (Data processing)
- `tokio` (Async runtime)
- `tonic` (gRPC framework)
- `sqlx` (Database access)
- `serde` (Serialization)

## 🐛 Troubleshooting

### Poetry issues
```bash
# Clear Poetry cache
poetry cache clear . --all

# Rebuild lock file
rm poetry.lock
poetry lock
poetry install
```

### Rust compilation issues
```bash
# Clean build
cargo clean

# Update dependencies
cargo update

# Check for platform-specific issues
rustup update
```

### Pre-commit hook issues
```bash
# Reinstall hooks
pre-commit uninstall
pre-commit install

# Run hooks on all files
pre-commit run --all-files
```

## ✨ Next Steps

1. Configure your IDE with Rust and Python support
2. Explore the codebase in `mosaicod/` and `mosaico-sdk-py/`
3. Run the tests to ensure everything is working
4. Check out the [documentation](https://docs.mosaico.dev) to understand the architecture
5. Start working on your contributions!

---

**Questions?** Check the [Documentation](https://docs.mosaico.dev) or reach out on [Discord](https://discord.gg/mwQtFnsckE).
