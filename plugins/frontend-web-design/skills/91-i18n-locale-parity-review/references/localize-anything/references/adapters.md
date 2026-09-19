# Adapters

## Role

Adapters are deterministic helpers for discovering, extracting, comparing,
validating, and rebuilding localization resources. They are not the product
architecture and do not replace the Coding Agent's understanding of the
project.

Prefer:

1. the project's native i18n tooling and conventions;
2. an existing Localize Anything handler when its documented boundary matches;
3. direct Coding Agent edits with explicit limitations when no handler fits.

Do not add a new framework, dependency, registry, trust tier, or plugin system
just to process a format the Coding Agent can safely handle with existing
project tools.

## Hard Constraints

When an adapter is used, preserve:

- resource keys and stable identities;
- placeholders and ICU branches;
- markup and escapes;
- comments or metadata required for round-trip safety;
- encoding and newline behavior where relevant;
- target-only content unless deletion is explicitly intended;
- source-project safety.

Unsupported syntax must be preserved or surfaced for review. Do not guess at a
destructive rewrite.

## Current Reusable Handlers

The repository currently contains handlers for:

- JSON locale files;
- YAML and TOML localization scalars;
- Android XML;
- Apple `.strings`, `.stringsdict`, and `.xcstrings`;
- PO/POT;
- XLIFF;
- CSV, TSV, and XLSX;
- Markdown and HTML visible text;
- SRT and WebVTT;
- Word OpenXML.

See `docs/adapters.md` for exact current implementation boundaries. Existing
format count does not imply that every framework, dynamic surface, asset, or
locale behavior is supported.

## v1 Priority

The first simplified CLI tier prioritizes JSON, YAML, Android XML, Apple
`.strings`, `.xcstrings`, PO/POT, and XLIFF. Other existing handlers may remain
available, but workflow quality, review quality, and lower human review cost
take priority over expanding format count.

## Capability Degradation

If a deterministic handler cannot safely process the input:

- let the Coding Agent use the project's own tooling or make scoped edits;
- record which checks were not available;
- retain the file or unit for manual/Agent review;
- do not claim structural coverage that was not verified.
