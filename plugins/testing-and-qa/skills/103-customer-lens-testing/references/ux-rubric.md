# Customer-Lens UX, Motion, and Polish Rubric

## 1. Foundations & Expertise Checklists

### Theoretical Foundations
- **ISO 9241-11:2018 (*Ergonomics of human-system interaction — Part 11: Usability*):** Defines usability as **effectiveness** (accuracy and completeness), **efficiency** (resources expended for results), and **satisfaction** (comfort and acceptability) in a specified context of use.
- **Jakob Nielsen (*Usability Engineering*, 1993; NN/g *Usability 101*, 2012):** Decomposes usability into five attributes that trade off across user maturity: **Learnability**, **Efficiency**, **Memorability**, **Errors**, and **Satisfaction**.
- **Alan Cooper (*About Face*, 4th ed., Wiley, 2014, Ch. 2–3):** Formulates the tri-modal distribution of **Beginners**, **Perpetual Intermediates** (the majority of paying customers), and **Experts**.
- **Cooper's Intermediate Trap (2014):** Teams must avoid both the **Beginner Trap** (unskippable wizards and stripped views that slow intermediates on day 2+) and the **Expert Trap** (top-level cockpit clutter that intimidates beginners).
- **Cooper's Design Rule (2014):** Optimize the primary workspace for perpetual intermediates while providing a gentle ramp for beginners and unobtrusive accelerators for experts.

### Level A — Complete Beginner Checklist (`B1`–`B5`, Zero Prior Context)
- [ ] **`B1` — 5-Second Value & Primary Action Clarity:** Within 5 seconds of landing, one unmistakable primary CTA uses user-domain verbs rather than internal system nouns (NN/g Heuristic #2 *Match Between System and the Real World*, 2024).
- [ ] **`B2` — Actionable Empty States:** Empty states state what belongs there, why it matters, and offer a 1-click starter action or sample dataset so the user never stares at a blank table or canvas (NN/g *Designing Empty States in Complex Applications*, 2021).
- [ ] **`B3` — Frictionless Onboarding & Deferred Walls:** The user reaches a First Value artifact before encountering complex configuration forms, secondary settings, or unskippable multi-step tours (Cooper *About Face*, 2014; Apple HIG *Onboarding*).
- [ ] **`B4` — Safe Exploration & Reversibility:** Mistaken clicks on primary or secondary controls can be backed out or undone immediately without losing starter progress (NN/g Heuristic #3 *User Control and Freedom*, 2024).
- [ ] **`B5` — Zero Unexplained Jargon:** Domain-specific, credit, or billing terms are explained inline via microcopy or hover/tap tooltips at the exact point of choice (NN/g Heuristic #6 *Recognition Rather Than Recall*, 2024).

### Level B — Perpetual Intermediate Checklist (`I1`–`I5`, Regular Returning Customer)
- [ ] **`I1` — Routine Workflow Step Economy:** The top 3 recurring tasks finish from the main workspace in `<= 3` view transitions without passing through beginner onboarding prompts or promotional banners (Cooper *About Face*, 2014, Ch. 3).
- [ ] **`I2` — State & Preference Persistence:** The UI remembers last-used filters, sort order, view mode (grid/list), panel widths, and form defaults across sessions (NN/g Heuristics #6 & #7, 2024).
- [ ] **`I3` — Shallow Progressive Disclosure (`<= 2` Levels):** Secondary parameters open in 1 click (popover, drawer, or accordion) rather than buried `>= 3` levels deep in global Settings (Jakob Nielsen, NN/g *Progressive Disclosure*, 2006/2024).
- [ ] **`I4` — Resumability & Draft Safety (Interrupted Session Test):** Closing a tab or switching views mid-form auto-saves or cleanly recovers the draft state upon return (ISO 9241-11:2018 Effectiveness).
- [ ] **`I5` — Scannable Status & History:** A returning user can immediately see what ran, succeeded, failed (with actionable retry), and queued without opening each item individually (NN/g Heuristic #1 *Visibility of System Status*, 2024).

### Level C — Domain Expert Checklist (`E1`–`E5`, High-Volume Power User)
- [ ] **`E1` — Command Palette & Keyboard Completeness (`Cmd/Ctrl+K`):** Every primary navigation target and high-frequency action triggers via keyboard shortcuts or a fuzzy Command Palette with shortcut hints (`Cmd+K`, `E`, `Del`) in menus and tooltips (NN/g Heuristic #7 *Accelerators*, 2024; W3C WCAG 2.2 SC 2.1.1 *Keyboard*).
- [ ] **`E2` — Multi-Select & Bulk Operations:** Every list, table, or media grid supports `Shift+Click` range selection, `Cmd/Ctrl+A` select all, and batch actions (delete, tag, export, retry) without per-item confirmation modals (Cooper *About Face*, 2014; NN/g *Bulk Actions*).
- [ ] **`E3` — High Information Density & Custom Views:** Experts can switch to a compact/table view, pin custom filter presets, or inspect raw metadata without decorative cards wasting 70% of the viewport (Edward Tufte, *The Visual Display of Quantitative Information*; Cooper, 2014).
- [ ] **`E4` — Non-Blocking Asynchronous Execution:** Long-running jobs move immediately to a background queue or toast so the expert can fire the next 10 jobs without waiting on a blocking spinner (ISO 9241-11:2018 Efficiency; NN/g *Response Times: The 3 Important Limits*, 1993/2024).
- [ ] **`E5` — Data Portability, API/Webhook/MCP & Deep Linking:** URLs hold shareable filter/item state and outputs export cleanly as JSON, CSV, Markdown, cURL, or programmatic API/MCP hooks (NN/g Heuristic #7 *Flexibility and Efficiency of Use*, 2024).

## 2. Complexity-Preserving Simplification & Component Polish (`P1`–`P5`)

### Simplification Rules (Keeping Scope and Elegance)
- **Tesler's Law (Larry Tesler, Xerox PARC; Dan Saffer, 2009; Jon Yablonski, *Laws of UX*, 2020/2024):** Every application has irreducible complexity that must be absorbed by system defaults and staged disclosure rather than feature deletion.
- **Smart Defaults & Hick's Law (Hick & Hyman, 1952; NN/g *The Power of Defaults*, 2005):** Decision time grows as $RT = a + b \log_2(n + 1)$, so pre-populate 80–90% of configuration fields with optimal defaults while keeping 100% of parameters inside an expandable drawer.
- **Contextual Progressive Disclosure (NN/g, 2006/2024):** Surface secondary toolbars and format flags only when contextually active (such as showing batch controls when `>= 1` item is selected).
- **Optimistic Undo Over Confirmation Modals (Cooper, 2014; NN/g *Confirmation Dialogs*, 2018):** Replace routine `"Are you sure?"` modals with immediate execution plus a `5–10s` `[Undo]` toast or soft-delete trash.
- **High-Cost Confirmation Guardrail (NN/g, 2018):** Reserve blocking confirmation modals strictly for irreversible, high-cost actions using specific verb labels (`"Delete Workspace"`, never `"OK"` or `"Yes"`).
- **Strong Information Scent (Pirolli & Card, *Psychological Review* 106(4), 643–675, 1999; NN/g *Information Scent*):** Label controls with explicit domain nouns (`"Export & API (CSV, JSON, Webhook)"`) rather than mystery icons or vague `"More..."` links.

### Anti-Patterns of Over-Simplification (Never Propose)
- **Feature Amputation:** Deleting advanced filters, batch actions, or raw parameters to reduce DOM nodes (violates Tesler's Law).
- **Mystery-Meat Icon-Only Chrome:** Replacing labeled controls with unlabeled icons (`...`) that force hover-hunting (destroys Information Scent).
- **Deep Drawer Burying (`> 2` Levels):** Hiding daily intermediate controls inside `Settings -> Advanced -> Preferences` (violates Cooper 2014 and NN/g `<= 2`-level disclosure).
- **Mandatory Linear Wizards for Repeat Tasks:** Splitting a routine 4-field form into a 4-screen step-by-step wizard (Cooper's Beginner Trap).
- **Low-Contrast Ultra-Minimal Chrome:** Removing input borders, dividers, and focus rings below W3C WCAG 2.2 SC 1.4.11 (`>= 3:1` non-text contrast) and SC 2.4.7 (*Focus Visible*).

### Component Polish Checklist (`P1`–`P5`, `vercel-labs/agent-skills` `MIT`, `pbakaus/impeccable` `Apache-2.0`)
- [ ] **`P1` — Complete Interactive State Matrix:** Every interactive element implements `default`, `:hover` guarded by `@media (hover: hover) and (pointer: fine)`, `:focus-visible` (`>= 3:1` contrast, `2px` width, `2px` offset), `:active` (`scale(0.98)` or luminance shift within `80ms–120ms`), and `:disabled` (reduced opacity, `cursor: not-allowed`, and reason tooltip).
- [ ] **`P2` — Loading & Skeleton Stability:** Buttons lock double-submission with an inline spinner and zero width/height jump, fetches under `150ms` skip skeleton flashes, and skeletons match loaded geometry (`CLS = 0.00`).
- [ ] **`P2b` — Error & Success State Integrity:** Inline field errors (`aria-describedby`) state exact cause and fix without wiping user input (NN/g *Reporting Errors in Forms*, 2016/2024), and success states use non-blocking morphs or auto-dismissing toasts.
- [ ] **`P3` — Hit Targets & Tabular Numerals:** Interactive targets meet W3C WCAG 2.2 SC 2.5.8 minimum `24x24 CSS px` (`44x44 CSS px` on touch per Apple HIG), and dynamic counters, timers, balances, and prices set `font-variant-numeric: tabular-nums`.
- [ ] **`P4` — Typography & Spatial Rhythm:** Layouts align to a `4px`/`8px` grid with concentric border radii ($R_{\text{outer}} = R_{\text{inner}} + \text{padding}$), `text-wrap: balance` on headings, and `text-wrap: pretty` within a `45–75ch` measure on body copy.
- [ ] **`P5` — Dark Mode Surface & Contrast Discipline:** Dark mode communicates elevation via progressive surface luminance steps and `1px solid rgba(255, 255, 255, 0.08)` hairline borders rather than dark drop shadows, satisfying WCAG 2.2 SC 1.4.3 (`>= 4.5:1` normal text, `>= 3:1` large text) without pure `#FFFFFF` on `#000000` halation.

## 3. Motion Rules & Live / Video Audit Protocols

### Quantitative Motion Rules (Apple HIG *Motion*; Material Design 3 *Motion*; Emil Kowalski, `emilkowalski/skills` `MIT`)
- **UI Chrome Ceiling (`< 300ms`):** Micro-interactions, button press/hover, switches, and tooltips run in `50ms–200ms` (Kowalski `100ms–150ms`, M3 `short1`–`short4`), popovers, menus, modals, and drawers in `180ms–250ms` (M3 `medium1`–`medium4` `250ms–400ms`), and full-screen layout transitions in `400ms–600ms` (M3 `long1`–`long4`).
- **Asymmetric Easing:** Entrances decelerate (`ease-out`, M3 `emphasized-decelerate` `cubic-bezier(0.05, 0.7, 0.1, 1.0)` or `cubic-bezier(0, 0, 0, 1)`), exits accelerate (`ease-in`, M3 `emphasized-accelerate` `cubic-bezier(0.3, 0.0, 0.8, 0.15)` or `cubic-bezier(0.3, 0, 1, 1)`) at `150ms–200ms`, and on-screen movement uses `cubic-bezier(0.2, 0.0, 0, 1.0)`.
- **Scale Origin & Spatial Continuity:** Animate modals, dropdowns, and popovers from `opacity: 0; transform: scale(0.95)` (range `0.93–0.97`, never `scale(0)`) anchored to the trigger `transform-origin`, and reverse the entrance vector on dismissal.
- **Compositor-Only Properties:** Animate strictly `transform` (`translate`, `scale`, `rotate`) and `opacity` (or GPU-composited `clip-path`/`filter`), and never `width`, `height`, `top`, `left`, `margin`, or `padding`.
- **Interruptibility:** Transitions and springs must preserve velocity and smoothly reverse when retargeted mid-flight (open -> close -> open within `80ms`).
- **Reduced Motion (W3C WCAG 2.2 SC 2.3.3 & CSS Media Queries Level 5):** Under `prefers-reduced-motion: reduce`, replace spatial translation, scaling, and bounce with a `100ms–150ms` opacity cross-fade while keeping state feedback intact.

### Live Session & 60fps Video Audit Protocols
- **Live DOM Audit (`microsoft/playwright`, `ChromeDevTools/chrome-devtools-mcp`):** Query `document.getAnimations()` and `effect.getKeyframes()` during interaction to flag non-composited layout properties, UI transitions `> 300ms`, `linear` or `ease-in` entrances, missing `transform-origin`, mid-flight snap on an `80ms` toggle, or broken `page.emulateMedia({ reducedMotion: 'reduce' })` behavior.
- **60fps Screen Recording Scrub (`16.67ms` per frame):**
  - *Input-to-pixel latency ($f_0 \to f_1$):* `<= 3 frames` (`<= 50ms`) instantaneous, `4–12 frames` (`67ms–200ms`) acceptable (`INP` Good), and `> 12 frames` (`> 200ms`) lag.
  - *Asymmetry & frame drops:* Verify entrance $F_{\text{in}} \approx 10–18\text{ frames}$ (`165ms–300ms`) with largest displacement in the first 4 frames, exit $F_{\text{out}} \approx 8–12\text{ frames}$ (`130ms–200ms`), and zero duplicate-frame stutters.
  - *Pre/post-transition layout jump:* Compare bounding boxes at $f_0$ and $f_{\text{end}}+1$ to catch `1–4px` reflow jumps or missing `scrollbar-gutter: stable`.

## 4. Runtime Metrics, Lostness ($L$), and Evidence-Anchored UMUX-Lite

### Core Web Vitals & Frame Telemetry (`web.dev`, `GoogleChrome/web-vitals` & `lighthouse` `Apache-2.0`, `dequelabs/axe-core` `MPL-2.0`)
| Metric | Collection API / Method | Good Threshold | Needs Improvement | Poor / Fail |
| :--- | :--- | :--- | :--- | :--- |
| **INP** (Interaction to Next Paint) | `PerformanceObserver` (`type: 'event'`) / `web-vitals` | **`<= 200ms`** | `200ms–500ms` | **`> 500ms`** |
| **CLS** (Cumulative Layout Shift) | `PerformanceObserver` (`type: 'layout-shift'`) | **`<= 0.10`** | `0.10–0.25` | **`> 0.25`** |
| **LoAF** (Long Animation Frames) | `PerformanceObserver` (`type: 'long-animation-frame'`, Chrome 123+) | **`0` frames `> 50ms`** | `1–2` frames (`50–100ms`) | **Any frame `>= 100ms`** |
| **Frame Pacing / Jank Rate** | CDP `Tracing.start` (`devtools.timeline`) / `rAF` @ 60Hz | **`< 1%` dropped** | `1%–5%` dropped | **`> 5%` dropped** |

### Behavioral Signals, Lostness ($L$), and Evidence-Anchored UMUX-Lite
- **Task Success Rate (`ISO 9241-11:2018` Effectiveness):** Score each task as `1.0` (Complete Success on intended path), `0.75` (Success with Friction: `>= 1` backtrack, error recovery, or `> 1.5x` optimal steps), `0.50` (Assisted/Workaround Success), or `0.0` (Failure/Abandonment).
- **UI Time Separation (`ISO 9241-11:2018` Efficiency):** Partition $T_{\text{total}} = T_{\text{agent\_inference}} + T_{\text{UI\_execution}} + T_{\text{app\_response}}$ and attribute only $T_{\text{UI\_execution}} + T_{\text{app\_response}}$ to the product.
- **Smith's Lostness Metric ($L$) (Paul A. Smith, *Interacting with Computers* 8(4), 365–381, 1996):**
  $$L = \sqrt{\left(\frac{N}{S} - 1\right)^2 + \left(\frac{R}{N} - 1\right)^2}$$
  where $R$ = minimum optimal unique views/states, $N$ = unique views/states visited, and $S$ = total view/state transitions including backtracks (`L = 0.00` perfect path $S = N = R$; `L < 0.40` low confusion; `L >= 0.40` measurably lost/confused; `L > 0.50` severe disorientation).
- **LLM Psychometric Calibration (Lu et al., `UXAgent`, CHI EA 2025 / `arXiv:2502.12561`):** Unanchored LLM Likert scores suffer positivity bias and near-zero severity reliability (Krippendorff's $\alpha \approx 0$ vs. defect detection Cohen's $\kappa \approx 0.50–0.52$).
- **Evidence-Anchored UMUX-Lite (Lewis, Utesch, & Maher, CHI 2013; Brooke, *SUS*, 1996):** Start `Item 1` (*capabilities meet requirements*) and `Item 2` (*easy to use*) at `7` (`1–7` scale), deduct `-1` per backtrack, `-1` per unrecovered validation error, `-1` if $L \ge 0.40$, and `-1` if `INP > 200ms` or `CLS > 0.10`, and compute $\text{UMUX-Lite}_{\text{SUS-eq}} = 0.65 \times \left(\frac{(\text{Item}_1 - 1) + (\text{Item}_2 - 1)}{12} \times 100\right) + 22.9$ (never reported as a human psychometric score).
- **Paired Competitor Benchmark:** Execute the identical task brief, input payload, and starting state on a live competitor and compare Task Completion (`0.0–1.0`), Steps ($S/R$), Lostness ($L$), Clicks + Keystrokes ($K$), Modals Hit, and Worst `INP`/`CLS`.

## 5. Five-Dimension Scoring Rubric & Priority Formula ($P$)

### Five-Dimension Rubric (`1–5` Anchored Scale; `Scope Kept < 4` Blocks Acceptance)
| Score | 1. Ease of Use (Efficiency & Flow) | 2. Confusion Resistance (Clarity & Scent) | 3. Motion Quality (Timing, Physics, A11y) | 4. Component Polish (States, Rhythm, Theme) | 5. Scope Kept (Capability Preservation) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **5 — Exemplary** | Optimal path ($S = R$); effortless beginner `TTFV`; full expert keyboard/batch accelerators (`Cmd+K`, multi-select). | $L < 0.15$; strong information scent; zero unexplained jargon; smart defaults cover 90% of cases; Undo replaces routine modals. | All transitions `< 300ms` (`100–250ms` UI); decelerate in / accelerate out; `transform` & `opacity` only; interruptible; `INP <= 100ms`; `prefers-reduced-motion` cross-fade. | All 8 states (`default`, `hover`, `focus-visible`, `active`, `disabled`, `loading`, `empty`, `error`) crafted; `CLS = 0.00`; `tabular-nums`; concentric radii; dark/light parity. | 100% of power features, edge parameters, exports, and batch controls remain accessible within `<= 2` disclosure clicks. |
| **4 — Strong (Release Ready)** | $S \le 1.2 R$; at most 1 minor extra click for beginner or expert; zero blocking friction. | $L < 0.30$; clear labels; minor secondary setting takes 1 extra look without backtracking. | Transitions `< 300ms`; `INP <= 200ms`; zero layout-property animations; `prefers-reduced-motion` honored. | All critical states present; `CLS <= 0.05`; hit targets `>= 24px` (`44px` touch); minor `1–2px` spacing or border tweak needed. | 100% of capabilities preserved; at most 1 advanced control is 2 clicks away instead of 1. |
| **3 — Acceptable (Needs Polish)** | $S \le 1.5 R$; routine flow works for intermediates, but lacks expert batch/shortcuts or has a clunky beginner start. | $L \in [0.30, 0.40)$; occasional ambiguous icon or routine confirmation modal interrupting flow. | Some transitions `300–400ms` or generic `ease`/`linear`; `INP` `200–300ms`; reduced-motion partially missing. | Missing `:focus-visible` or `:active` on some controls; spinner flashes; `CLS` `0.05–0.10`; minor dark-mode contrast weakness. | Core capabilities intact, but an advanced option is buried 3 levels deep or requires a manual workaround. |
| **2 — Friction-Heavy** | $S > 1.5 R$; repetitive manual steps; blocking spinners lock the UI during jobs. | $L \in [0.40, 0.55)$; mystery-meat icons; jargon blocks beginners; form errors wipe input or show cryptic codes. | Janky layout animations (`width`/`height`); uninterruptible transitions `> 400ms`; `INP` `300–500ms`; no reduced-motion support. | Missing empty/error states; `CLS` `0.10–0.25`; stuck hover states on touch; WCAG contrast failures. | Simplification hid or broke a secondary workflow needed by intermediates or experts. |
| **1 — Broken / Hostile** | Task fails or requires external help; severe Beginner or Expert trap. | $L > 0.55$; circular navigation or dead-end screens. | Severe stutter (`INP > 500ms`, `LoAF > 100ms`); vestibular motion that cannot be disabled. | Unstyled/raw errors, overlapping text, `CLS > 0.25`, or keyboard trap. | Features stripped or inaccessible; loss of product scope. |

### Scope-Guarded Priority Formula ($P$)
$$P = \frac{\text{Severity} \times \text{PersonaWeight} \times \text{Frequency}}{\text{ImplementationEffort}} \times \mathbb{I}(\text{ScopeKept} = 1)$$
- **$\mathbb{I}(\text{ScopeKept} = 1) \in \{0, 1\}$:** Hard gate where $P = 0$ (rejected) if a proposal removes any existing user capability or expert parameter rather than defaulting or disclosing it.
- **$\text{Severity} \in \{1..4\}$:** `4` (`blocker`: data loss/Keyboard Trap/`CLS > 0.25`/`INP > 500ms`), `3` (`high`: friction where $L \ge 0.40$, missing empty state blocking `TTFV`, missing batch action forcing $10\times$ clicks, layout-animation jank), `2` (`medium`: polish or flow, modal replaceable by Undo, missing `:focus-visible`/`:active`, duration outside `100–300ms`, missing `tabular-nums`), `1` (`low`: micro-refinement, optical alignment, concentric radii $R_{\text{outer}} = R_{\text{inner}} + \text{padding}$, surface luminance).
- **$\text{PersonaWeight}$:** `3.0` (All 3 Tiers), `2.5` (Perpetual Intermediates), `2.0` (Beginners / First Value), `1.5` (Experts Only).
- **$\text{Frequency}$:** `3` (Every Session / Core Loop), `2` (Weekly), `1` (Rare / Setup).
- **$\text{ImplementationEffort}$:** `1` (CSS/Token/Copy `< 30m`), `2` (Component State/Disclosure `1–3h`), `3` (Architectural/Flow Change `> 3h`).

## 6. Public Sources
- **Standards & Accessibility:** ISO 9241-11:2018 (`iso.org/standard/63500.html`); W3C WCAG 2.2 (`w3.org/TR/WCAG22/`, SC 1.4.3, 1.4.11, 2.1.1, 2.3.3, 2.4.7, 2.5.8); Google Chrome `web.dev` (`inp`, `cls`, `loaf`); EU Directive (EU) 2023/2673 Art. 11a.
- **UX & Interaction Design:** Alan Cooper et al., *About Face* (4th ed., Wiley, 2014, Ch. 2–3); Jakob Nielsen, *Usability Engineering* (1993) and NN/g (*10 Usability Heuristics* 1994/2024, *Progressive Disclosure* 2006/2024, *Usability 101* 2012, *Confirmation Dialogs* 2018, *Information Scent*, *Empty States* 2021, *Form Errors* 2016/2024); Peter Pirolli & Stuart K. Card, *Information Foraging* (*Psychological Review* 106(4), 1999); Larry Tesler & Hick & Hyman (1952) in Jon Yablonski, *Laws of UX* (O'Reilly, 2020/2024); Edward Tufte, *The Visual Display of Quantitative Information*; C. Wharton et al., *Cognitive Walkthrough* (1994); K. A. Ericsson & H. A. Simon (1984); Noriaki Kano et al. (1984); C. Christensen (2016) & A. Ulwick (2005).
- **Metrics & LLM-User Research:** Paul A. Smith, *Lostness* (*Interacting with Computers* 8(4), 365–381, 1996); John Brooke, *SUS* (1996); James R. Lewis et al., *UMUX-Lite* (ACM CHI 2013, pp. 2099–2102); Yuxuan Lu et al., *UXAgent* (`neuhai/UXAgent`, `MIT`, CHI EA 2025, `arXiv:2502.12561`) & *AgentA/B* (`arXiv:2504.09723`, 2025); Xiang et al., *SimUser* (CHI 2024, `DOI:10.1145/3613904.3642481`); Park et al. (`arXiv:2411.10109`, 2024); Hämäläinen et al. (CHI 2023, `DOI:10.1145/3544548.3580688`); Agnew et al. (CHI 2024, `DOI:10.1145/3613904.3642703`).
- **Motion & Open-Source Audit Tools:** Apple HIG *Motion* (`developer.apple.com/design/human-interface-guidelines/motion`); Google Material Design 3 *Motion* (`m3.material.io/styles/motion/easing-and-duration/tokens-specs`); Emil Kowalski, *Animations on the Web* (`emilkowal.ski`, `emilkowalski/skills` `MIT`); `pbakaus/impeccable` (`Apache-2.0`); `vercel-labs/agent-skills` (`MIT`) & `vercel-labs/agent-browser` (`Apache-2.0`); `garrytan/gstack` (`MIT`); `phuryn/pm-skills` (`MIT`); `alirezarezvani/claude-skills` (`MIT`); `anthropics/skills` (`Apache-2.0`); `ChromeDevTools/chrome-devtools-mcp` (`Apache-2.0`); `microsoft/playwright` (`Apache-2.0`); `dequelabs/axe-core` (`MPL-2.0`); `GoogleChrome/lighthouse` & `GoogleChrome/web-vitals` (`Apache-2.0`).
