# On windows
#   Install MSYS2 https://www.msys2.org/
#   SET PATH=%PATH%;C:\msys64\usr\bin;C:\msys64
#   (to install make: pacmman -S make)

PROJECT = acbox
ROOT_DIR := $(dir $(realpath $(lastword $(MAKEFILE_LIST))))
SOURCES := support/checks-and-balances.py src tests
BUILDDIR := build
GDOT = $(shell tput setaf 2)●$(shell tput sgr0)
RDOT = $(shell tput setaf 1)x$(shell tput sgr0)

export PYTHONPATH=$(ROOT_DIR)/src


# self-documentation magic: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Display the list of available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


.PHONY: check
check: ## ruff check + lint
	ruff check $(SOURCES)
	ruff format --check $(SOURCES)
	dmypy run -- $(SOURCES)
	@echo "$(GDOT) [$@] pass"

.PHONY: fmt
fmt:  ## format code (ruff check --fix), updating source files
	ruff format $(SOURCES)
	ruff check --fix $(SOURCES)

.PHONY: lint
lint:  ## run the linter (mypy) and report errors.
	@mypy src tests && echo "$(GDOT) mypy check pass" || echo "$(RDOT) mypy check failed"

.PHONY: tests
tests:  ## run all tests
	pytest -vvs tests

.PHONY: coverage
coverage:  ## run all tests with coverage
	mkdir -p $(BUILDDIR)
	pytest -vvs \
        --cov=$(PROJECT) \
        --cov-report=html:$(BUILDDIR)/coverage --cov-report=term \
        --html=$(BUILDDIR)/junit.html --self-contained-html \
        tests

.PHONY: clean
clean:  ## clean all artifacts
	@rm -rf .dmypy.json src/acbox.egg-info dist $(BUILDDIR)
	@rm -rf projects/info/dist projects/repotool/dist
	@python support/clean.py $(SOURCES)
	@echo "$(GDOT) cleaned"
