# Community Skills & Agents (third-party, attributed)

Third-party skills and agents redistributed from open-source projects, kept separate from
Skillry's original work under `plugins/`. Every source uses a permissive license (MIT) and
is credited in full.

| Source | Standalone skills | Merged into hubs (3.0.0) | Agents | License |
|---|--:|--:|--:|---|
| [github/awesome-copilot](github-awesome-copilot/) | 0 | 17 | 0 | MIT |
| [wshobson/agents](wshobson-agents/) | 1 | 44 | 0 | MIT |
| [Donchitos/Claude-Code-Game-Studios](Donchitos-Claude-Code-Game-Studios/) | 0 | 23 | 49 | MIT |
| [addyosmani/agent-skills](addyosmani-agent-skills/) | 2 | 5 | 0 | MIT |
| [addyosmani/web-quality-skills](addyosmani-web-quality-skills/) | 0 | 2 | 0 | MIT |
| [jaktestowac/awesome-copilot-for-testers](jaktestowac-awesome-copilot-for-testers/) | 0 | 4 | 0 | MIT |

Each source directory keeps its original `LICENSE` and a short `README.md`. Full notices:
[`../NOTICE`](../NOTICE) and [`../THIRD-PARTY-NOTICES.md`](../THIRD-PARTY-NOTICES.md).

**Why separate?** `plugins/` is Skillry's own authored, deepened, permission-bounded content.
`community/` is curated external content redistributed with credit. Keeping them apart makes
provenance and licensing unambiguous.

**Merged content (3.0.0).** Skillry 3.0.0 merged overlapping skills into skill hubs. Third-party
skills absorbed by a hub live under that hub's `references/<former-name>.md` (plus
`references/<former-name>/`, and `scripts|templates|assets|examples/<former-name>/` when present),
with a provenance header and the upstream `LICENSE` copied beside the content. A hub can therefore
sit under `plugins/` and still contain attributed third-party references, and the two remaining
`addyosmani/agent-skills` hubs contain references from other sources (and two Skillry originals).
Each source README lists where its merged skills went; [`../THIRD-PARTY-NOTICES.md`](../THIRD-PARTY-NOTICES.md)
lists the sources imported in 3.0.0.

**Excluded:** Content under the OpenAI Services Agreement (openai/skills) is **not** redistributed.
