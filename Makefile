# On windows
#   Install MSYS2 https://www.msys2.org/
#   SET PATH=%PATH%;C:\msys64\usr\bin;C:\msys64
#   (to install make: pacmman -S make)

ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
SOURCES=release/checks-and-balances.py src tests

export PYTHONPATH=$(ROOT_DIR)/src


# self-documentation magic
help: ## Display the list of available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: check
check: ## ruff check + lint
	ruff check $(SOURCES)
	ruff format --check $(SOURCES)
	dmypy run -- $(SOURCES)
	@echo "🟢 [$@] pass"

.PHONY: fmt
fmt:  ## Format code (ruff check --fix), updating source files
	ruff format $(SOURCES)
	ruff check --fix $(SOURCES)

.PHONY: lint
lint:  ## Runs the linter (mypy) and report errors.
	@mypy src tests && echo "🟢 mypy check pass"


.PHONY: clean
clean:  ## clean all artifacts
	@rm -rf .dmypy.json src/acbox.egg-info dist
	@python release/clean.py $(SOURCES)
	@echo "🟢 cleaned"
