# VC Analyst Agent – Design

## 1. Persona

**VC Analyst Agent**: A virtual analyst with 10+ years in venture capital, focused on **B2B enterprise**.  
The agent:

- Interprets **research theses** (e.g. “PLG SaaS in dev tools”, “vertical AI in healthcare”).
- Suggests **structured attributes** (company size, stage, investors, etc.) that match the thesis.
- Produces **qualitative heuristics** (search/match logic) used for scraping and filtering.
- Is RAG‑ready (knowledge base) and later fine‑tunable.

---

## 2. Inputs & Outputs

### 2.1 Input: Research Thesis

Free‑text from the user describing:

- **What** kinds of companies they want (sector, business model, wedge).
- **Why** (thesis, trends, conviction).
- **Rough focus** (e.g. stage, geography) if known.

**Example:**

> “We’re looking for PLG SaaS companies in dev tools and infra. Seed to Series A, US‑first. Strong technical founders, early traction with developers. We like companies that could become default in a category.”

### 2.2 Output: Analyst Suggestions

1. **Suggested attributes** (editable by user):

   | Attribute          | Description                    | Example values                          |
   |--------------------|--------------------------------|-----------------------------------------|
   | Company size       | Employees / revenue band       | "10–50", "50–200", "$1M–$10M ARR"       |
   | Funding stage      | Stage(s) of interest           | Seed, Series A, Series B                 |
   | Target investors   | VC / angels to look for        | a16z, Sequoia, YC alumni                 |
   | Geography          | HQ / markets                   | US, US + EU, etc.                        |
   | Industry / vertical| Sectors                        | Dev tools, vertical AI, fintech          |
   | Exclusions         | Sectors / models to skip       | Consumer, crypto, hardware               |

2. **Heuristics (qualitative match logic)**

   Short, structured text used as **filter criteria** for:

   - Scraper/validator (e.g. stage, geo).
   - AI filter (semantic + LLM matching).

   Example:

   > “B2B SaaS, PLG motion. Dev tools or infra. Seed–Series A. US‑based. Technical founders, early dev traction. Exclude consumer, crypto, pure services.”

---

## 3. Flow

1. User writes **Research thesis** in the UI.
2. User clicks **“Get analyst suggestions”** → backend calls VC Analyst Agent.
3. Agent returns **suggested attributes** + **heuristics**.
4. User reviews/edits attributes (and optionally heuristics).
5. User runs **“Search” / “Filter”**:
   - Scraper uses **attributes** (stage, geo, etc.) to pre‑filter.
   - AI filter uses **heuristics** (and optional RAG) to rank/match.

---

## 4. Implementation Notes

### 4.1 Backend

- **`vc_analyst_agent`** (or `VCAnalystAgent`):
  - Input: `research_thesis: str`.
  - Output: `suggested_attributes: dict`, `heuristics: str`.
  - Uses LLM + fixed **system prompt** (B2B enterprise, 10+ years VC).
  - Structured output (e.g. JSON) for attributes.

- **API**: `POST /research/thesis/suggest`  
  - Request: `{ "thesis": "…" }`.  
  - Response: `{ "suggested_attributes": {…}, "heuristics": "…" }`.

### 4.2 UI

- **Research Thesis** section (e.g. on Run Setup or Analyst page):
  - Textarea: “Research thesis”.
  - Button: “Get analyst suggestions”.
  - Form: **Suggested attributes** (pre‑filled, editable).
  - Display **heuristics** (editable or read‑only).
  - “Use for search” → pass attributes + heuristics into scraper and filter.

### 4.3 Scraper / Filter Wiring

- **Scraper** (validator, config):
  - Map suggested attributes → `stage`, `location`, `valuation_min/max`, `exclude_industries`, etc.
- **Filter** (existing AI filter):
  - Use **heuristics** as `criteria` (same as current “filter criteria”).
  - Optional: pass attributes as extra context.

### 4.4 RAG & Fine‑tuning (later)

- **RAG**: Inject retrieved chunks (e.g. from VC knowledge base) into the analyst’s context when generating attributes + heuristics.
- **Fine‑tuning**: Optional future step to adapt the analyst’s style or vertical (e.g. healthcare vs dev tools).

---

## 5. Heuristics / Qualitative Feedback

The analyst encodes **qualitative judgment** in:

1. **Suggested attributes** → structured filters (stage, size, geo, etc.).
2. **Heuristics** → natural‑language match logic used by the AI filter.

User can:

- Edit both before running search.
- (Future) Give feedback (thumbs up/down, edits) to improve suggestions over time.

---

## 6. Phase 1 vs Later

### Phase 1 (done)

- **Research thesis** → VC Analyst → **suggested attributes** + **heuristics**.
- UI: Research Thesis & VC Analyst section (Run Setup); "Get analyst suggestions" → editable attributes + heuristics.
- **"Use heuristics as filtering criteria"** → copies heuristics into Step 3 criteria → **existing AI filter** uses them.
- API: `POST /research/thesis/suggest`; backend module `app.analyst.vc_analyst_agent`.

### Later

- **Scraper wiring**: Use suggested attributes (stage, geography, etc.) to override `COMPANY_FILTERS` when running a scrape (e.g. optional body on `POST /research/scrape`).
- Fine‑tuning.
- Full RAG integration (design is RAG‑ready; wiring can follow).
- Learning from user feedback (storage, model updates).
