# Makefile for C library project
.DELETE_ON_ERROR:

PROJECT := @PROJECT@
SOVERSION ?= 1
VERSION ?= $(SOVERSION).0.0

ifeq ($(origin CC),default)
CC := gcc
endif
CC ?= gcc
AR ?= ar
RANLIB ?= ranlib
CFLAGS ?= -Wall -Wextra -O2
PICFLAGS ?= -fPIC
RM ?= rm -f

SRCDIR := src
BUILDDIR := build
OBJDIR := $(BUILDDIR)/obj

SOURCES := $(wildcard $(SRCDIR)/*.c)
OBJECTS := $(SOURCES:$(SRCDIR)/%.c=$(OBJDIR)/%.o)
DEPENDS := $(OBJECTS:.o=.d)

STATIC_LIB := $(BUILDDIR)/lib$(PROJECT).a
SHARED_LIB := $(BUILDDIR)/lib$(PROJECT).so.$(VERSION)

.PHONY: all static shared clean help

## Build both static and shared libraries
all: static shared

## Build static library
static: $(STATIC_LIB)

## Build shared library
shared: $(SHARED_LIB)

$(STATIC_LIB): $(OBJECTS)
	@mkdir -p $(@D)
	$(AR) rcs $@ $^
	$(RANLIB) $@

$(SHARED_LIB): $(OBJECTS)
	@mkdir -p $(@D)
	$(CC) $(LDFLAGS) -shared -Wl,-soname,lib$(PROJECT).so.$(SOVERSION) $^ $(LDLIBS) -o $@

$(OBJDIR)/%.o: $(SRCDIR)/%.c
	@mkdir -p $(@D)
	$(CC) $(CPPFLAGS) $(CFLAGS) $(PICFLAGS) -MMD -MP -c $< -o $@

-include $(DEPENDS)

## Clean build artifacts
clean:
	$(RM) -r "$(BUILDDIR)"

## Show help
help:
	@printf '%s\n' 'all: Build both libraries' 'static: Build the static library' 'shared: Build the shared library' 'clean: Remove build artifacts' 'help: Show this help'
