# GNU Make C++ executable scaffold; review against the actual project before use.
.DEFAULT_GOAL := all
.DELETE_ON_ERROR:
.SUFFIXES:

PROJECT := @PROJECT@
CXX ?= c++
CPPFLAGS ?=
CXXFLAGS ?= -std=c++20 -O2 -Wall -Wextra
LDFLAGS ?=
LDLIBS ?=

SOURCES := $(sort $(wildcard src/*.cpp src/*.cc src/*.cxx))
OBJECTS := $(addprefix build/obj/,$(addsuffix .o,$(SOURCES)))
DEPENDS := $(OBJECTS:.o=.d)
TARGET := build/$(PROJECT)

.PHONY: all clean help

all: $(TARGET)

$(TARGET): $(OBJECTS)
	@mkdir -p "$(@D)"
	$(CXX) $(CXXFLAGS) $(LDFLAGS) $(OBJECTS) $(LDLIBS) -o "$@"

build/obj/%.o: %
	@mkdir -p "$(@D)"
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c "$<" -o "$@"

-include $(DEPENDS)

clean:
	$(RM) -r -- "build"

help:
	@printf '%s\n' 'all: Build the executable' 'clean: Remove build outputs' 'help: Show these targets'
