# Makefile for C project
SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
.SUFFIXES:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PROJECT := @PROJECT@

ifeq ($(origin CC),default)
CC := gcc
endif
CC ?= gcc
CFLAGS ?= -Wall -Wextra -O2
RM ?= rm -f

SRCDIR := src
BUILDDIR := build
OBJDIR := $(BUILDDIR)/obj

SOURCES := $(wildcard $(SRCDIR)/*.c)
OBJECTS := $(SOURCES:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
DEPENDS := $(OBJECTS:.o=.d)
TARGET := $(BUILDDIR)/$(PROJECT)

.PHONY: all clean help

## Build the application (default)
all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p $(@D)
	$(CC) $(LDFLAGS) $^ $(LDLIBS) -o $@

$(OBJDIR)/%.o: $(SRCDIR)/%.c
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) -MMD -MP -c $< -o $@

-include $(DEPENDS)

## Remove build artifacts
clean:
	$(RM) -r "$(BUILDDIR)"

## Show help
help:
	@printf '%s\n' 'all: Build the application' 'clean: Remove build artifacts' 'help: Show this help'
