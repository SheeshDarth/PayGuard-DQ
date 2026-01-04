# PayGuard DQ

**GenAI Agent for Universal, Dimension-Based Data Quality Scoring in Payments**

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Revanthm2027/payguard-dq)

A hackathon-ready, end-to-end prototype for automated data quality scoring of payment transactions using a multi-agent architecture.

## 🎯 Overview

This system provides **universal, dimension-based data quality scoring** specifically designed for payment transaction data. It uses 7 specialized agents to profile datasets, identify quality dimensions, execute checks, score quality, explain results, and generate remediation plans—all while maintaining strict compliance with **no raw data storage**.

### Key Features

- ✅ **7 Quality Dimensions**: Completeness, Uniqueness, Validity, Consistency, Timeliness, Integrity, Reconciliation
- 🤖 **7 Specialized Agents**: Profiler, Dimension Selector, Check Executor, Scoring, Explainer, Remediation, Test Export
- 🔒 **No Raw Data Storage**: Only metadata, aggregates, and scoring outputs are persisted
- 📊 **Full Explainability**: Per-dimension scores with metrics, error rates, and failing checks
- 🎯 **Payments-Specific**: Reconciliation dimension for settlement ledger and BIN map validation
- 🔧 **LLM-Optional**: Works with deterministic templates or OpenAI-compatible LLMs
- 📦 **One-Command Deploy**: Docker Compose for instant setup

---

## 🏗️ Architecture

### System Flow

```
Dataset Upload → Profiler Agent → Dimension Selector Agent → Check Executor Agent
                                                                      ↓
Governance Report ← Test Export Agent ← Remediation Agent ← Scoring Agent
                                                                      ↓
                                                              Explainer Agent
```

### Agent Responsibilities

1. **Profiler Agent**: Analyzes schema and computes aggregate statistics (NO raw data in output)
2. **Dimension Selector Agent**: Automatically identifies applicable quality dimensions based on dataset profile
3. **Check Executor Agent**: Runs all checks for selected dimensions (completeness, uniqueness, validity, consistency, timeliness, integrity, reconciliation)
4. **Scoring Agent**: Computes per-dimension and risk-weighted composite scores with full explainability
5. **Explainer Agent**: Generates human-readable narratives (LLM or deterministic stub mode)
6. **Remediation Agent**: Creates prioritized recommendations with impact scoring and phased plans
7. **Test Export Agent**: Generates dbt tests and Great Expectations suite

### Technology Stack

- **Backend**: Python FastAPI + pandas + SQLModel + SQLite
- **Frontend**: Next.js 14 (App Router) + TypeScript + Tailwind CSS + Recharts
- **Storage**: SQLite (metadata-only)
- **Deployment**: Docker Compose

---

## 📋 Task Fulfillment

### Task 1: Governed Input Handling ✅

- **POST /api/ingest**: Upload dataset file (multipart)
- **POST /api/ingest-reference**: Upload reference files (BIN map, currency rules, MCC codes, settlement ledger)
- Dataset processed **in-memory only** and discarded after scoring
- Only metadata artifacts stored (dataset fingerprint, schema, profiling aggregates, check results, scores)

### Task 2: Automatic Dimension Identification ✅

Dimension Selector Agent uses deterministic + explainable logic:
- **Completeness**: Always applicable
- **Uniqueness**: If ID-like columns detected (high cardinality + naming patterns)
- **Validity**: If currency/country/MCC/amount columns detected
- **Consistency**: If multiple related fields detected (status+settlement_date, timestamps)
- **Timeliness**: If timestamp columns detected
- **Integrity**: If reference datasets provided
- **Reconciliation**: If settlement ledger or BIN map provided (payments differentiator)

Output includes selected dimensions + rationale per dimension.

### Task 3: Per-Dimension + Composite Scoring with Explainability ✅

**Per-Dimension Scoring**:
- Formula: `score = max(0, 100 * (1 - weighted_error_rate))`
- Weighted error rate computed from check failures with severity weights
- Explainability payload includes:
  - Metrics used
  - Error rates
  - Top failing checks
  - Impacted columns
  - Score formula

**Composite Scoring**:
- Risk-weighted formula: `composite = sum(dim_score * dim_weight) / sum(dim_weight)`
- Dimension weights based on payments criticality model:
  - Financial-critical fields (amount, currency, txn_id): weight 3
  - Ops-critical fields (merchant_id, mcc, country): weight 2
  - Regulatory-critical fields (customer_id, kyc): weight 3
- Output shows dim_weight rationale

**Minimum Checks Implemented**:
1. **Completeness**: null rates, required fields
2. **Uniqueness**: duplicate detection on inferred keys
3. **Validity**: ISO4217 currency, ISO3166 country, 4-digit MCC, amount >= 0 with outlier detection
4. **Consistency**: status→settlement_date, currency decimals, event_time ≤ settlement_time
5. **Timeliness**: event lag vs SLA, processing delay
6. **Integrity**: referential presence checks (merchant_id, customer_id)
7. **Reconciliation**: BIN match rate, settlement ledger match (txn_id, amount, currency)

### Task 4: Prioritized Recommendations ✅

Remediation Agent output:
- **top_issues[]** ranked by `impact * frequency * criticality`
- Each issue includes:
  - What failed, where (columns), severity
  - Business impact category (Financial/Operational/Regulatory)
  - Probable root causes
  - Actionable fix steps
  - Expected score gain (simulated)
- **remediation_plan**: Phased (P0 immediate, P1 next sprint, P2 backlog)
- **ticket_payloads**: Jira-like JSON (optional)

### Task 5: UI ✅

Frontend features:
- **Upload Interface**: Dataset + optional reference files
- **Runs List**: All past runs with metadata
- **Run Detail View** with tabs:
  - **Overview**: Donut chart for dimension scores, line chart for trend, composite DQS
  - **Issues**: Table with severity, dimension, columns, evidence metrics, recommended action
  - **Actions**: Download buttons (dbt tests, GE suite, governance report), remediation plan display
  - **Agent Logs**: Timeline of agent execution steps with inputs/outputs

### Task 6: Compliance & Governance ✅

**Governance Report** includes:
- Confirms "no raw data persisted"
- Lists exactly what is stored (tables + fields)
- Shows dataset hash, run timestamp, model version
- Full audit trail of agent steps
- Redaction policy: LLM only sees aggregates (never row-level values)
- Retention policy section (configurable days)

**Storage Verification**:
- SQLite tables: runs, dimension_scores, check_results, agent_logs, references, artifacts
- NO raw transaction rows
- Artifacts directory: only JSON/YAML/MD files

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- (Optional) Python 3.11+ for running sample data generator locally

### 1. Generate Sample Data

```bash
# Install Python dependencies (if running locally)
pip install pandas numpy

# Generate sample datasets
python scripts/generate_sample_data.py
```

This creates:
- `sample_data/transactions_batch1.csv` (good quality, ~95% DQS)
- `sample_data/transactions_batch2.csv` (bad quality, ~70% DQS with specific issues)
- `sample_data/bin_reference.csv`
- `sample_data/currency_rules.csv`
- `sample_data/mcc_codes.csv`
- `sample_data/settlement.csv`

### 2. Start Services

```bash
# Create .env file (optional, for LLM support)
cp .env.example .env
# Edit .env and add OPENAI_API_KEY if desired

# Start backend + frontend
docker-compose up --build
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Run Demo Script

#### Upload Batch 1 (Good Quality)

1. Go to http://localhost:3000
2. Upload `sample_data/transactions_batch1.csv`
3. Upload reference files:
   - BIN Map: `sample_data/bin_reference.csv`
   - Currency Rules: `sample_data/currency_rules.csv`
   - MCC Codes: `sample_data/mcc_codes.csv`
   - Settlement Ledger: `sample_data/settlement.csv`
4. Click "Upload & Process Dataset"
5. **Expected Result**: DQS ~95%, minimal issues

#### Upload Batch 2 (Bad Quality)

1. Upload `sample_data/transactions_batch2.csv` (with same reference files)
2. **Expected Result**: DQS ~70%, top issues:
   - 0.8% duplicate txn_id (uniqueness)
   - 3-5% missing auth_code (completeness)
   - Invalid MCC codes (validity)
   - JPY currency decimal mismatches (consistency)
   - Event lag spikes beyond SLA (timeliness)
   - Unknown BINs (reconciliation)
   - Settlement ledger mismatches (reconciliation)

#### Download Exports

1. Go to run detail page
2. Click "Actions" tab
3. Download dbt tests YAML
4. Download Great Expectations suite JSON
5. View governance report confirming no raw storage

---

## 📊 API Documentation

### Ingestion

**POST /api/ingest**
- Upload dataset file (CSV)
- Returns: `{run_id, message, row_count, column_count}`

**POST /api/ingest-reference**
- Upload reference file (CSV)
- Body: `reference_file`, `reference_type` (bin_map | currency_rules | mcc_codes | settlement_ledger)
- Returns: `{reference_id, reference_type, row_count, message}`

### Runs

**GET /api/runs**
- List all runs
- Returns: `{runs: [{run_id, dataset_name, row_count, column_count, timestamp, status, composite_dqs}]}`

**GET /api/runs/{run_id}**
- Get full result bundle
- Returns: `{run, scores, checks, narrative, remediation, agent_logs}`

**GET /api/runs/{run_id}/export/dbt**
- Download dbt tests YAML

**GET /api/runs/{run_id}/export/ge**
- Download Great Expectations suite JSON

**GET /api/runs/{run_id}/governance**
- Get governance report
- Returns: `{run_id, report (markdown), format}`

---

## 🔍 Sample Data Issues (Batch 2)

The bad quality batch (`transactions_batch2.csv`) contains these intentional issues:

| Issue | Dimension | Rate | Impact |
|-------|-----------|------|--------|
| Duplicate txn_id | Uniqueness | 0.8% | Financial |
| Missing auth_code | Completeness | 3-5% | Operational |
| Invalid MCC codes | Validity | 3% | Operational |
| Invalid currency codes | Validity | 5% | Financial |
| Invalid country codes | Validity | 5% | Operational |
| JPY decimal errors | Consistency | 5% | Financial |
| Missing settlement_date for SETTLED | Consistency | 3% | Financial |
| Event lag > 24h SLA | Timeliness | varies | Operational |
| Unknown BINs | Reconciliation | 5% | Financial |
| Settlement ledger mismatches | Reconciliation | 1-2% | Financial |

---

## 🛠️ Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Run Tests

```bash
# Backend unit tests (if implemented)
cd backend
pytest

# Frontend type checking
cd frontend
npm run lint
```

---

## 📁 Project Structure

```
/
├── backend/
│   ├── app/
│   │   ├── agents/              # 7 specialized agents
│   │   ├── checks/              # Check implementations for 7 dimensions
│   │   ├── routes/              # API routes
│   │   ├── utils/               # Hashing, governance
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # SQLModel schemas
│   │   ├── storage.py           # Database layer
│   │   └── orchestrator.py      # Agent pipeline
│   ├── artifacts/               # Metadata outputs only
│   ├── data/                    # SQLite database
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/
│   │   ├── runs/                # Runs pages
│   │   ├── page.tsx             # Home/upload page
│   │   ├── layout.tsx
│   │   └── globals.css
│   ├── lib/
│   │   └── api.ts               # API client
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   └── generate_sample_data.py  # Sample data generator
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🎓 Key Design Decisions

### 1. Metadata-Only Storage

**Why**: Compliance with data governance policies, no PII/sensitive data persistence.

**How**: 
- Dataset processed in-memory using pandas
- Only aggregates, statistics, and check results stored
- Dataset fingerprint (SHA256) used for tracking

### 2. Agentic Architecture

**Why**: Modularity, explainability, extensibility.

**How**:
- Each agent has single responsibility
- Agents produce structured outputs (JSON)
- Orchestrator coordinates execution
- All agent steps logged for audit trail

### 3. Payments-Specific Reconciliation

**Why**: Differentiate from generic DQ tools.

**How**:
- BIN map validation (card issuer/network)
- Settlement ledger matching (txn_id, amount, currency)
- Match rate scoring with severity levels

### 4. Risk-Weighted Composite Scoring

**Why**: Not all dimensions equally important for payments.

**How**:
- Criticality model based on field types
- Financial-critical fields weighted higher
- Dimension weights shown in explainability

### 5. LLM-Optional Design

**Why**: Hackathon reliability + future extensibility.

**How**:
- Explainer Agent detects API key availability
- Falls back to deterministic templates
- Same interface for both modes

---

## 🚧 Future Enhancements

- [ ] Real-time streaming ingestion
- [ ] Multi-dataset comparison
- [ ] Automated remediation execution
- [ ] Integration with dbt Cloud / GE Cloud
- [ ] Custom dimension definitions
- [ ] ML-based anomaly detection
- [ ] Multi-tenancy support

---

## 📝 License

This is a hackathon prototype. Use at your own discretion.

---

## 🙏 Acknowledgments

Built for Problem Statement 3: "GenAI Agent for Universal, Dimension-Based Data Quality Scoring in Payments"

**Tech Stack**: FastAPI, Next.js, SQLModel, Recharts, Tailwind CSS, Docker
