# Variable and configuration contracts

Inspect the actual Makefile graph and variable origins before changing defaults.
In GNU Make, `?=` assigns only when a variable is undefined. An explicitly empty
environment or command-line value is still defined. Preserve an intentional
empty value; if the build requires a nonempty tool setting, report that contract
rather than silently substituting a compiler. Built-in defaults also count as
definitions.

Ordinary Makefile assignments, including `+=`, do not append to a variable set
on the command line. Keep required project options separate from user-replaceable
flags and pass both explicitly where needed. An `override` assignment is another
deliberate policy choice, not a generic fix: use it only when the project requires
those options despite user overrides. Check an actual command-line override and
a compile that needs a project include path, not merely the variable's text.

Prerequisite names normally expand while Make reads the rules. A target-specific
`TARGET` assignment does not retroactively change a previously expanded
prerequisite or declare a new output path. Compute paths from a configuration
selected before those rules are read, or define the configuration graphs
explicitly. Give debug, release and other incompatible configurations distinct
objects, dependency files and final outputs. Target-specific flags on a shared
prerequisite can also make its result depend on which parent builds it first.

Build configurations in both orders and inspect the executable's actual behavior.
A successful `make release` after `make debug` does not prove that release code
was rebuilt. Separate directories do not automatically track later changes to
flags within the same configuration: retain a real configuration-dependency
mechanism or rebuild affected outputs when those values change.

In mixed C/C++ builds, distinguish source paths and language extensions in object
and dependency names. Mapping both `src/helper.c` and `src/helper.cpp` to
`build/helper.o` loses a translation unit. Compile each language with its proper
driver and settings; link C++ objects through the C++ driver. Verify a fixture
that requires symbols from both equal-stem sources, not only an empty build.
The optional scaffold here supports C++ sources only; mixed-language projects
need their own rules.

Clearing `.SUFFIXES` clears suffix rules; it does not disable every built-in
pattern rule. When evaluating an explicit graph, inspect the active rule database
or use `--no-builtin-rules` deliberately and check that the declared rules still
build the intended outputs. In the reviewed GNU Make 4.3 fixture, clearing
suffixes removed the implicit C-object link, while RCS checkout patterns remained
in the database. Database inspection did not execute a checkout command. Do not
infer every rule's behavior from one missing implicit build.

These contracts are supported by the versioned GNU Make 4.4.1 manual and selected
native GNU Make 4.3/GCC 13.3 controls on Linux. They do not qualify arbitrary
configurations, mixed-language projects, other compilers, native Windows builds
or coding-agent effectiveness.
