# VC-Stack v2 Micro-Step Plan

STEP 0 — Safety & Baseline (do this first)
0.1 Create a new git branch: feature/v2-deal-workspace
0.2 Run the app and confirm v1 works end-to-end (upload Excel → filter → results)
0.3 Add a CHANGELOG_V2.md and write: "Starting VC-Stack v2 build"
0.4 Add a folder: vc-stack-v2-spec/ and save a copy of this plan as micro_steps.md

STEP 1 — Add New Database Models (no UI yet)
Goal: Create "Deal Workspace" objects in DB. No UI changes.
1.1 Open backend/app/models.py
1.2 Add a new SQLAlchemy model: Deal
fields: id, name, source, owner, sector, stage, status, created_at
1.3 Add a new model: Memo
fields: id, deal_id(FK), memo_type, version, json_payload(JSON/text), generated_by_agent, confidence_score, created_at
1.4 Add a new model: Risk
fields: id, deal_id(FK), risk_type, description, severity, mitigation, created_at
1.5 Add a new model: Decision
fields: id, deal_id(FK), verdict, rationale, conditions, decided_at
1.6 Add a new model: DataRoomDocument
fields: id, deal_id(FK), filename, doc_type, source, embedding_id, created_at
1.7 Add a new model: ExternalSource
fields: id, deal_id(FK), url, source_type, embedding_id, created_at
1.8 Add a new model: ResearchFinding
fields: id, deal_id(FK), category, source_type, content, citation, created_at
1.9 Open backend/app/database.py
1.10 Ensure Base.metadata.create_all(bind=engine) will create these tables.
1.11 Add a simple script backend/app/init_db.py that imports models and runs create_all.
1.12 Run: python backend/app/init_db.py
1.13 Confirm new tables exist (SQLite file or DB).
✅ Stop here. Commit: chore: add v2 db models (deal, memo, risk, decision, docs, research)

STEP 2 — Add Minimal FastAPI Endpoints for Deals (CRUD-lite)
Goal: Create deals + list deals + get deal.
2.1 Create a new file: backend/app/schemas_v2.py
2.2 Define Pydantic schemas:
DealCreate, DealRead
MemoCreate, MemoRead
RiskCreate, RiskRead
DecisionCreate, DecisionRead
DataRoomDocumentCreate, ExternalSourceCreate, ResearchFindingCreate
2.3 In backend/app/main.py create a new router section:
POST /v2/deals → create deal
GET /v2/deals → list deals
GET /v2/deals/{deal_id} → get deal
2.4 In each endpoint:
open DB session
write minimal create/list/get
return Pydantic response
2.5 Run FastAPI locally, test with curl or browser.
✅ Commit: feat(api): add v2 deal endpoints

STEP 3 — Add Streamlit "Deal Workspace" Skeleton Page
Goal: UI creates and selects deals. No research yet.
3.1 Open streamlit_app.py
3.2 Add a sidebar section: Deal Workspace (v2)
3.3 Add a "Create Deal" form:
name, source, owner, sector, stage
submit calls POST /v2/deals
3.4 Add a "Select Deal" dropdown:
fetch deals from GET /v2/deals
store selected deal_id in st.session_state["deal_id"]
3.5 Display the selected deal metadata on screen.
✅ Commit: feat(ui): add deal workspace skeleton

STEP 4 — Attach Data Room Upload to a Deal (reuse your ingestion)
Goal: Upload documents + store them as deal-linked DataRoomDocument.
4.1 Create a new UI section "Data Room Upload" visible only when a deal is selected
4.2 Reuse existing upload component (PDF/MD/TXT)
4.3 When user uploads a file:
run your existing document_ingestion.py → chunk → embed → store in document_store.py
capture returned embedding_id or document key
4.4 After ingestion completes:
call new endpoint POST /v2/deals/{deal_id}/data-room-docs
store filename, doc_type, embedding_id, source="company"
4.5 Add new endpoints in FastAPI:
POST /v2/deals/{deal_id}/data-room-docs
GET /v2/deals/{deal_id}/data-room-docs
4.6 In UI, show a table of uploaded docs for that deal.
✅ Commit: feat: link data room ingestion to deals

STEP 5 — Add "External Sources" Capture (URLs) to a Deal
Goal: Save URLs; ingest later.
5.1 Add a UI box "External Research URLs"
input URL
dropdown source type (report/news/academic/database/other)
submit calls API
5.2 Add FastAPI endpoints:
POST /v2/deals/{deal_id}/external-sources
GET /v2/deals/{deal_id}/external-sources
5.3 Store URL + source_type; leave embedding_id null for now.
✅ Commit: feat: add external sources tracking

STEP 6 — Build External Research Ingestion (simple: static web first)
Goal: Fetch URL → extract text → chunk/embed → store → link embedding_id.
6.1 In a new file external_research_ingestion.py:
function fetch_and_extract(url) using requests + BeautifulSoup
clean text
return text + citation (url)
6.2 Reuse chunk/embed logic from document_ingestion.py
6.3 Store chunks in your document_store.py (same store is fine, but tag metadata source="external" and url)
6.4 Add an API endpoint:
POST /v2/deals/{deal_id}/external-sources/{source_id}/ingest
fetch URL
chunk/embed/store
update ExternalSource.embedding_id
create ResearchFinding records if you want (optional now)
6.5 Add a Streamlit button next to each URL: "Ingest"
calls endpoint above
shows success message
✅ Commit: feat: external research ingestion (static web)

STEP 7 — Add "Thesis Builder" (simple rubric v1)
Goal: Save thesis/rubric per deal (or global).
7.1 Add a new DB model ThesisProfile
id, deal_id (nullable if global), sectors, must_haves, red_flags, stage_targets, weights(json)
7.2 Add endpoints:
POST /v2/deals/{deal_id}/thesis
GET /v2/deals/{deal_id}/thesis
7.3 Streamlit UI:
multi-line text boxes for must_haves / red_flags
sliders or numeric inputs for weights (market, team, traction, moat, strategic_fit)
✅ Commit: feat: thesis builder v1

STEP 8 — Implement DataRoom Analyst Agent (structured JSON only)
Goal: Agent reads ONLY data room chunks → outputs facts, metrics, gaps.
8.1 Create agents/data_room_analyst.py
8.2 Input:
deal_id
retrieved RAG chunks from data room docs only
8.3 Output JSON schema:
{
  "extracted_facts": {...},
  "metrics_found": {...},
  "inconsistencies": [...],
  "missing_information": [...]
}
8.4 Enforce JSON response validation
8.5 Save output to ResearchFinding records (source_type="data_room", category="facts")
✅ Commit: feat: data room analyst agent

STEP 9 — Implement External Research Agent (structured JSON + citations)
Goal: Agent reads ONLY external chunks → market/competition/risk reality check.
9.1 Create agents/external_research_agent.py
9.2 Input:
deal_id
retrieved chunks only from external sources
9.3 Output JSON:
{
  "market_size": {"value": "...", "growth": "...", "citations": [...]},
  "competition": [{"name": "...", "notes": "...", "citations": [...]}],
  "regulatory_notes": [...],
  "citations": [...]
}
9.4 Save to ResearchFinding (source_type="external")
✅ Commit: feat: external research agent

STEP 10 — Screening Memo Generator (IEC format)
Goal: Produce a Screening memo with verdict + confidence + why-not.
10.1 Create agents/screening_memo_agent.py
10.2 Inputs:
thesis profile
data room findings
external research findings
10.3 Output JSON schema (your screening schema)
10.4 Save to Memo table with memo_type="screening", version=1
10.5 Streamlit button: "Generate Screening Memo"
shows memo nicely formatted
stores JSON in DB
✅ Commit: feat: screening memo generation

STEP 11 — Risk Register + Diligence Questions Agent
Goal: Produce risk table + "deal killer" questions.
11.1 Create agents/risk_diligence_agent.py
11.2 Output JSON:
risks list (type, severity, mitigation)
diligence_questions
killer_questions
11.3 Save risks into Risk table.
✅ Commit: feat: risk register + diligence engine

STEP 12 — IC Memo Generator (v1)
Goal: Full IC memo JSON, using both inside-out and outside-in.
12.1 Create agents/ic_memo_agent.py
12.2 Inputs:
thesis profile
screening memo
risk register
data room + external summaries
12.3 Output IC memo JSON schema
12.4 Save to Memo table memo_type="ic"
12.5 Streamlit button: "Generate IC Memo"
✅ Commit: feat: IC memo v1 generation

STEP 13 — Decision Logging UI
Goal: Record proceed/hold/pass with rationale and conditions.
13.1 Streamlit section "IC Decision"
verdict dropdown
rationale text
conditions bullets
submit calls API → store in Decision
✅ Commit: feat: IC decision logging

STEP 14 — Hardening (micro-quality)
Goal: Make outputs reliable.
14.1 Add JSON schema validation for every agent output
14.2 Add "citation required" checks for external agent and IC memo
14.3 Add a "confidence score must be 0–1" check
14.4 Add prompt regression test script with 3–5 sample deals
✅ Commit: chore: validation + minimal regression tests.
