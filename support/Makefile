PYTHON := python3
THISDIR := $(PWD)
BUILDDIR := ../build/support.build

# self-documentation magic
help: ## Display the list of available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: pack
pack:  ## pack the builder.pyz
	@rm -rf $(BUILDDIR)
	@mkdir -p $(BUILDDIR)
	@cp builder.py $(BUILDDIR)/__main__.py
	@cp -r ../src/acbox $(BUILDDIR)
	@$(PYTHON) ./clean.py $(BUILDDIR)
	@cd $(BUILDDIR) && zip -r $(THISDIR)/builder.pyz .
