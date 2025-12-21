# self-documentation magic: http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html
help: ## Display the list of available targets
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

export PYTHONPATH = ../../src

.PHONY: pack
pack:  ## create self standing package
	../../support/packer.py -v -x info.py
	chmod a+rx dist/info.pyz
