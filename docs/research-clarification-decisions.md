# Clarification decisions: bounded review

The locked Trail of Bits `ask-questions-if-underspecified` entrypoint treats
multiple plausible interpretations as a reason to pause, and asks for
confirmation even when the user has explicitly said to proceed without
answers. Those rules can interrupt a task when repository evidence or an
existing user decision already supports an ordinary, reversible choice. The
same source correctly distinguishes questions answerable by a quick discovery
read from missing requirements that matter.

The experimental [clarify-when-needed overlay](../included/improved/skills/clarify-when-needed/SKILL.md)
separates a missing choice from authorization, preserves prior user decisions,
and continues work independent of a required unanswered question. It retains
the original source and full CC-BY-SA-4.0 license in the overlay package.
The immutable catalog mirror remains the comparison source.

[Zhang and Choi's clarification research](https://aclanthology.org/2025.findings-naacl.306/)
describes how the value of clarification depends on the user's preference for
speed versus carefulness and on plausible interpretations. Its evaluation
covered question answering, translation and natural-language inference, not
this repository's coding-agent workflow. Applying that tradeoff here is a
design inference, not evidence that this overlay improves coding performance.

## Evaluation still needed

Future independent agent trials should distinguish at least: a routine local
choice with an inferable project default; a consequential missing target; a
previously authorized action with complete inputs; a required unanswered
question alongside independent work; and a user correction after an assumption.
Tasks, expected outcomes and graders must be defined independently of the
skill's text. Retain both unnecessary interruptions and cases where an agent
acted on an unresolved consequential ambiguity. No such agent trial has been
run for this overlay; packaging validation is not behavioral validation.
