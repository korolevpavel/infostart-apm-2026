# Repository Guidelines

## Project Structure & Module Organization

This repository contains 1C Trade Management (`УправлениеТорговлей`) 11.6.2.68, targeting platform compatibility 8.3.27. Sources use Designer XML format.

- `src/Configuration.xml` declares configuration properties and registered objects.
- `src/Catalogs/`, `Documents/`, `CommonModules/`, and register directories contain metadata XML and object subdirectories with BSL modules and forms.
- `src/Ext/` contains application modules and configuration interfaces. Images and templates live under `CommonPictures/` and `CommonTemplates/`.
- `v8project.yaml` declares Unica source set `main`, rooted at `src/`.
- `openspec/specs/` holds specifications; `openspec/changes/` holds proposals and archived changes. `openspec/config.yaml` selects `spec-driven`.
- `build/` and `.build/` hold ignored runtime artifacts. No dedicated test suite is configured.

## Build, Test, and Development Commands

Use Unica MCP for 1C operations; these are tool calls, not shell commands:

- `unica.view {}` — discover source sets and configuration.
- `unica.check {}` — check workspace and repository readiness.
- `unica.check {"at":"main:Configuration"}` — validate configuration metadata; check changed objects separately.
- `unica.run {}` — inspect currently supported runtime operations and argument contracts before building, pushing, or launching.

For OpenSpec, run `openspec list` to list active changes and `openspec templates` to inspect workflow templates. Run `git diff --check` before submitting changes.

## Coding Style & Naming Conventions

Follow surrounding Russian BSL identifiers, tab indentation, regions, and client/server execution directives. Preserve existing copyright notices. Avoid unrelated formatting changes across the vendor export.

Keep metadata names, references, UUIDs, and configuration registrations consistent. Follow `.gitattributes`: XML and BSL use CRLF; YAML and Markdown use LF. No standalone formatter or linter is configured.

## Testing Guidelines

Run Unica validation for affected metadata and modules. Validation does not establish runtime correctness: exercise changed behavior in a development infobase and record inputs and outcomes. For posting changes, verify register movements and reversal behavior. No coverage threshold or test naming convention is established.

## Commit & Pull Request Guidelines

History uses concise Russian descriptions, such as `Добавлен конфиг OpenSpec`; Conventional Commits are not required. Keep commits focused.

Include the problem, affected objects, validation results, and runtime checks in PR descriptions. Link relevant issues or OpenSpec changes; attach screenshots for form changes.

Assistant-contributed commits require a trailer:

- Codex: `Co-Authored-By: codex <codex@openai.com>`
- Claude: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

## Local Configuration

Keep infobase connections and credentials in ignored `v8project.local.yaml`. Never commit local databases, `.local/`, build artifacts, or generated `src/ConfigDumpInfo.xml` and `src/DumpFilesIndex.txt`.
