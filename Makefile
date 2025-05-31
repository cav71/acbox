# On windows
#   Install MSYS2 https://www.msys2.org/
#   SET PATH=%PATH%;C:\msys64\usr\bin;C:\msys64
#   (to install make: pacmman -S make)

ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))

export PYTHONPATH=$(ROOT_DIR)/src


# self-documentation magic
help: ## Display the list of available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: check
check: check-fmt lint ## ruff check + lint
	@echo "🟢 pass"

.PHONY: check-fmt
check-fmt:  ## Runs ruff check
	@ruff check src tests && echo "🟢 ruff check pass"

.PHONY: fmt
fmt:  ## Format code (ruff check --fix), updating source files
	@ruff check --fix src tests
	@ruff format src tests

.PHONY: lint
lint:  ## Runs the linter (mypy) and report errors.
	@mypy src tests && echo "🟢 mypy check pass"
