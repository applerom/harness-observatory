# Lesson: Runtime Freshness And Agent Version Inertia

## Real Episode

During v0.1, the project was scaffolded on Python 3.12. Roman noticed that this looked like a model-memory choice, not a current-stable choice.

Codex checked official Python.org release pages on 2026-04-26 and found that Python 3.14.4 was the latest stable line, while Python 3.15 was still alpha. The project moved to `>=3.14,<3.15`, regenerated `uv.lock`, and revalidated the app on Python 3.14.4.

## Lesson

Agents often pick versions they have seen often in training. That can be reasonable, but it is not evidence that the version is current.

For runtimes, frameworks, and major dependencies:

- check a current primary source before pinning;
- update lockfiles, not only manifest files;
- validate under the runtime that the repo claims to support;
- record the reason when choosing latest stable rather than latest prerelease.

The same applies to local agent CLIs. A model name or flag shape may be valid in
one Codex session but unsupported by the installed CLI. Probe the actual command
with `--help` or a tiny no-op prompt before encoding it into an `AgentRunner`.

## Student Exercise

When reviewing an agent-generated project, ask:

- Which runtime did the agent choose?
- Is that choice current stable, conservative stable, or just familiar?
- Does the lockfile agree with the manifest?
- Did tests run under the claimed version?
