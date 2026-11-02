.PHONY: all prepare publish verify
.NOTPARALLEL:
STEP ?= printf '%s\n'

all: publish verify
publish verify: prepare

prepare publish verify:
	@$(STEP) $@
