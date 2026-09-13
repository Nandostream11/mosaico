#!/usr/bin/env bash

# Mosaico Developer Helper Script
# Run common development tasks

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    cat << EOF
Mosaico Development Helper

Usage: bash dev_helper.sh [COMMAND]

Commands:
  setup           Install all dependencies (Python + Rust)
  python-check    Run Python code quality checks (Ruff)
  python-test     Run Python tests with pytest
  python-format   Format Python code
  rust-check      Check Rust code for errors
  rust-test       Run Rust tests
  rust-clippy     Run Rust linter (Clippy)
  rust-fmt        Format Rust code
  test-all        Run all tests (Python + Rust)
  check-all       Run all code quality checks
  hooks-install   Install git pre-commit hooks
  help            Show this help message

Examples:
  bash dev_helper.sh setup
  bash dev_helper.sh python-test
  bash dev_helper.sh check-all
EOF
}

export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

cd_to_dir() {
    local dir=$1
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}Warning: Directory $dir not found${NC}"
        return 1
    fi
    cd "$dir"
}

# Python SDK Tasks
python_check() {
    echo -e "${BLUE}Running Python code quality checks...${NC}"
    cd_to_dir "mosaico-sdk-py" || return 1
    poetry run ruff check .
    poetry run ruff format --check .
    echo -e "${GREEN}✓ Python checks passed${NC}"
    cd - > /dev/null
}

python_test() {
    echo -e "${BLUE}Running Python tests...${NC}"
    cd_to_dir "mosaico-sdk-py" || return 1
    poetry run pytest
    echo -e "${GREEN}✓ Python tests passed${NC}"
    cd - > /dev/null
}

python_format() {
    echo -e "${BLUE}Formatting Python code...${NC}"
    cd_to_dir "mosaico-sdk-py" || return 1
    poetry run ruff format .
    poetry run ruff check --fix .
    echo -e "${GREEN}✓ Python code formatted${NC}"
    cd - > /dev/null
}

# Rust Tasks
rust_check() {
    echo -e "${BLUE}Checking Rust code for errors...${NC}"
    cd_to_dir "mosaicod" || return 1
    export SQLX_OFFLINE=true
    cargo check --workspace
    echo -e "${GREEN}✓ Rust check passed${NC}"
    cd - > /dev/null
}

rust_test() {
    echo -e "${BLUE}Running Rust tests...${NC}"
    cd_to_dir "mosaicod" || return 1
    export SQLX_OFFLINE=true
    cargo test --workspace
    echo -e "${GREEN}✓ Rust tests passed${NC}"
    cd - > /dev/null
}

rust_clippy() {
    echo -e "${BLUE}Running Rust linter (Clippy)...${NC}"
    cd_to_dir "mosaicod" || return 1
    export SQLX_OFFLINE=true
    cargo clippy --all-targets --all-features -- -D warnings
    echo -e "${GREEN}✓ Clippy checks passed${NC}"
    cd - > /dev/null
}

rust_fmt() {
    echo -e "${BLUE}Formatting Rust code...${NC}"
    cd_to_dir "mosaicod" || return 1
    cargo fmt --all
    echo -e "${GREEN}✓ Rust code formatted${NC}"
    cd - > /dev/null
}

# Setup
setup() {
    echo -e "${BLUE}🔧 Setting up Mosaico development environment...${NC}"
    
    echo -e "${BLUE}Installing Python SDK dependencies...${NC}"
    cd_to_dir "mosaico-sdk-py" || return 1
    poetry install
    cd - > /dev/null
    
    echo -e "${BLUE}Checking Rust environment...${NC}"
    export SQLX_OFFLINE=true
    rustc --version
    cargo --version
    
    echo -e "${GREEN}✓ Setup complete!${NC}"
}

# Install hooks
hooks_install() {
    echo -e "${BLUE}Installing git pre-commit hooks...${NC}"
    pre-commit install
    pre-commit run --all-files || echo -e "${YELLOW}Some files may need formatting${NC}"
    echo -e "${GREEN}✓ Hooks installed${NC}"
}

# Test all
test_all() {
    echo -e "${BLUE}Running all tests...${NC}"
    python_test || { echo -e "${YELLOW}Python tests failed${NC}"; }
    rust_test || { echo -e "${YELLOW}Rust tests failed${NC}"; }
    echo -e "${GREEN}✓ All tests completed${NC}"
}

# Check all
check_all() {
    echo -e "${BLUE}Running all code quality checks...${NC}"
    python_check || { echo -e "${YELLOW}Python checks failed${NC}"; }
    rust_check || { echo -e "${YELLOW}Rust checks failed${NC}"; }
    rust_clippy || { echo -e "${YELLOW}Rust clippy checks failed${NC}"; }
    echo -e "${GREEN}✓ All checks completed${NC}"
}

# Main
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

case "$1" in
    setup)
        setup
        ;;
    python-check)
        python_check
        ;;
    python-test)
        python_test
        ;;
    python-format)
        python_format
        ;;
    rust-check)
        rust_check
        ;;
    rust-test)
        rust_test
        ;;
    rust-clippy)
        rust_clippy
        ;;
    rust-fmt)
        rust_fmt
        ;;
    test-all)
        test_all
        ;;
    check-all)
        check_all
        ;;
    hooks-install)
        hooks_install
        ;;
    help)
        show_help
        ;;
    *)
        echo "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
