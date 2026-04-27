# Lesson: Visual QA Gives Agents Eyes

## Real Episode

Roman noticed two matrix UX problems:

- the wide comparison table had horizontal scroll only at the bottom;
- clicking a cell updated a detail region below the table, but the user stayed near the top and could not see the update.

The backend tests were green. The route tests were green. The UI was still awkward.

## Lesson

Agents must not build web UI blind. A local app needs agent-visible visual checks:

- deterministic browser automation for repeatable checks;
- screenshots when layout matters;
- DOM checks when interaction state matters;
- human feedback captured back into PRD, WHY graph, and lessons.

For this project, the default local UI QA tool is Playwright CLI. MCP browser connectors are useful for specific connected workflows, but they should not be the default because their tool schemas add context cost even when unused.

## Current Tooling Pattern

Use current primary docs when choosing the workflow. On 2026-04-26, OpenAI docs describe GPT-5.5 with the GA `computer` tool for flexible UI operation, while still recommending browser automation frameworks such as Playwright or Selenium as the fastest path for local browser automation.

Project rule:

- use Playwright CLI for routine local visual regression checks;
- use higher-level computer-use tooling when a task needs flexible screen-level interaction;
- record the decision when the tool choice may age quickly.

## Student Exercise

When an agent says "the UI works", ask for evidence:

- What viewport was checked?
- Is there a screenshot?
- Did the agent click the main interactive control?
- Did the page visibly move or update where a user can see it?
