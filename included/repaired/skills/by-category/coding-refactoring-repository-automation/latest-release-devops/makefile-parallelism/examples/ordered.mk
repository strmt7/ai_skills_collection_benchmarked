.PHONY: all prepare publish verify
STEP ?= printf '%s\n'

all: verify
verify: publish
publish: prepare

prepare publish verify:
	@$(STEP) $@
