# Development As Curriculum

Harness Observatory teaches agent work by being built with agents in public, durable steps.

## Principle

Real development problems are course material:

- stale model defaults, such as choosing an older runtime without checking current stable releases;
- subagent orchestration friction, such as thread limits and completed agents left open;
- documentation drift after fast implementation;
- integration catches that only the lead agent sees across slices;
- deliberate v0.x compromises that make feedback possible sooner.

The goal is not to pretend the process is perfect. The goal is to show how an agent-first project notices friction, records the decision, adapts the operating rule, and keeps moving.

## Operating Rule

When a development episode teaches something reusable:

1. Record the raw observation in `EVOLUTION.md`.
2. If it can help students, extract a short lesson under `docs/lessons/`.
3. Link decisions to evidence: command output, source docs, validation result, or a concrete file change.
4. Keep the lesson small enough to read during a live class.

## Why Students Need This

Students will not learn agent work from polished success stories alone. They need to see ordinary operator moves:

- ask whether the agent chose a version because it was current or because it was familiar;
- close completed subagents before raising concurrency;
- prefer a tiny shippable slice when the full version is still unclear;
- write down why a decision was made so a future agent can revise it safely.

This project treats those moves as first-class material.
