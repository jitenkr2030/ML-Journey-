# ReconcileAI — Pending Tasks
# Last Updated: 12 October 2026
# Status: Deployed on Deplexo + Free Tier Active

---

## 🟢 COMPLETED TODAY (12 October 2026)

- [x] Error Handling → Toast notifications (replace alert())
  - 9 alert() calls replaced with toastSuccess/toastError/toastInfo
  - Auto-dismiss after 3 seconds
  - CSS animations (slide-in)

- [x] Mobile Responsive → CSS media queries
  - Tablet breakpoint (768px)
  - Small phone breakpoint (480px)
  - Touch targets (44px/48px/52px min)
  - Tables horizontal scroll
  - Upload boxes stacked
  - Login/register modal responsive

- [x] Progress Feedback → Progress bar (bookkeeping)
  - Progress bar with percentage
  - 21 pipeline items with ✅❌⏭ icons
  - Live status updates during run
  - Animated progress fill with shine effect

- [x] Settings & Preferences → Auto-fill
  - ⚙️ Settings icon in nav
  - Modal: Business Name, GSTIN, Period, Email
  - localStorage persistence
  - Auto-fill GSTIN/period on all service forms
  - GSTIN validation (15 chars)

- [x] Reconciliation History → Save + view past work
  - PostgreSQL table (history)
  - history_service.py (save, list, delete, stats)
  - history.py routes (GET /api/history, DELETE /api/history/{id})
  - Auto-save BRS + GST results
  - 📋 History icon in nav
  - Modal: stats + past entries + delete
  - Search/filter

- [x] Client Management → Full CRUD
  - PostgreSQL table (clients)
  - client_service.py (add, update, delete, list, get, search)
  - clients.py routes (6 routes: CRUD + search + get one)
  - 👥 Clients icon in nav
  - Modal: list + add + edit + delete + search
  - Validation (GSTIN 15, PAN 10)
  - Status (active/inactive)
  - Initials avatar

- [x] Free Tier Setup (Frontend + Backend)
  - 2 free BRS/month, 1 free GST/month, 1 free UPI/month
  - Frontend: localStorage tracking + counters + paywall
  - Backend: PostgreSQL usage_tracking table
  - usage_service.py (check_limit, consume_usage, get_usage_status)
  - usage.py routes (GET /api/usage, POST /api/usage/check, POST /api/usage/consume)
  - Server-side enforcement in reconcile.py
  - Homepage: "✨ Start Free — No Credit Card Needed"
  - Free counters in demo section
  - Paywall: summary free, full report ₹499
  - Monthly auto-reset
  - Block after limit reached + upgrade prompt

- [x] Homepage Update (Pricing + Features)
  - Added UPI Reconciliation pricing card (₹499)
  - Added Complete Bookkeeping pricing card (₹2,999 + BEST VALUE badge)
  - Added 21 Pipeline Bookkeeping feature card
  - Added UPI Reconciliation feature card
  - Updated title: "Pay-per-use. ₹499 onwards."
  - Updated footer

- [x] Bookkeeping Progress Bar
  - Progress bar + 21 pipeline status items
  - ✅❌⏭ icons per pipeline
  - Animated progress fill

---

## 🔴 PRIORITY 1: Domain + Deployment (This Week)

- [ ] Buy domain: reconcileai.in (₹700-900/year on Cloudflare)
- [ ] Buy domain: reconcileai.com (₹1,000-1,200/year)
- [ ] Connect domain to Deplexo (CNAME → reconcileai.deplexo.com)
- [ ] Free SSL setup (Cloudflare)
- [ ] Test: reconcileai.in shows frontend
- [ ] Test: www.reconcileai.in shows frontend
- [ ] Upgrade Deplexo to Pro plan ($10/month)

---

## 🔴 PRIORITY 2: ML Model Improvement

### Data Expansion
- [ ] Collect more security company bank statements (more months)
- [ ] Collect more ledger data
- [ ] Get different bank formats (HDFC, ICICI, Axis)
- [ ] Get different business types (manufacturing, trading, retail)
- [ ] Collect UPI-heavy transaction patterns
- [ ] Collect edge cases (refunds, reversals, chargebacks)

### Model Upgrade
- [ ] Feature engineering from real data patterns
- [ ] Upgrade from Naive Bayes to XGBoost
- [ ] Target accuracy: 95% → 98%+
- [ ] Confidence calibration
- [ ] Smart file parser upgrade (PDF parsing - PyMuPDF)
- [ ] Scanned PDF support (OCR - Tesseract)
- [ ] Multi-sheet Excel handling
- [ ] Bank-specific format detection

---

## 🔴 PRIORITY 3: Self-Learning Engine

### Week 1: Feedback Collection
- [ ] Create feedback table (PostgreSQL)
- [ ] Build FeedbackCollector class (learning_engine.py)
- [ ] API endpoint: POST /api/feedback
- [ ] Frontend: 👍👎 buttons on match results
- [ ] Store user corrections

### Week 2: Pattern Memory
- [ ] Create patterns table (PostgreSQL)
- [ ] Build PatternMemory class
- [ ] Build knowledge_base.py (BankFormatDB, TransactionPatternDB, VendorDB, UserCorrectionDB, ErrorPatternDB)
- [ ] Pattern lookup before matching
- [ ] Pattern save after matching

### Week 3: Learning Engine
- [ ] Build IncrementalLearner class
- [ ] Learn from user corrections
- [ ] Update pattern weights
- [ ] Recalibrate confidence scores
- [ ] learning_engine.py complete

### Week 4: Auto-Retraining
- [ ] Build AutoRetrainer class
- [ ] Weekly background retrain
- [ ] Model evaluation (accuracy, precision, recall, F1)
- [ ] Auto-deploy if better
- [ ] Auto-rollback if worse
- [ ] Performance monitoring dashboard

---

## 🟡 PRIORITY 4: Tally Connector

### Phase 1: Local Agent (Week 1-3)
- [ ] tally_api.py — Tally XML HTTP client
- [ ] converter.py — ReconcileAI results → Tally XML
- [ ] Ledger mapping (fuzzy matching)
- [ ] app.py — Desktop GUI (tkinter)
- [ ] reconcile_client.py — Fetch from ReconcileAI cloud
- [ ] config.py — Settings (port, company name)
- [ ] installer.py — PyInstaller (.exe for Windows)
- [ ] Test with real Tally (ERP 9 + TallyPrime)

### Phase 2: TDL Plugin (Week 4-6)
- [ ] Custom menu in Tally: "🤖 ReconcileAI"
- [ ] HTTP call to ReconcileAI API
- [ ] Import vouchers directly in Tally
- [ ] Import history
- [ ] Testing on Tally ERP 9 + TallyPrime

### Pricing Integration
- [ ] Frontend: "Push to Tally (+₹300)" checkbox
- [ ] BRS ₹499 → BRS + Tally Push ₹799
- [ ] Bookkeeping ₹2,999 → + Tally Push ₹3,499
- [ ] Standalone connector: ₹4,999/year

---

## 🟡 PRIORITY 5: Security AI Integration

- [ ] API route: backend/app/routes/security.py
- [ ] POST /api/security/upload — Upload Excel files
- [ ] POST /api/security/run/{id} — Run 9 pipelines
- [ ] GET /api/security/status/{id} — Progress tracking
- [ ] GET /api/security/download/{id} — Download reports
- [ ] Frontend tab: "🔒 Security Audit"
- [ ] Upload: Attendance + Payroll Excel
- [ ] Progress bar (9 stages)
- [ ] Results dashboard
- [ ] Price: ₹4,999-₹19,999

---

## 🟢 PRIORITY 6: Bookkeeping Testing

- [ ] Test bookkeeping tab with real data (localhost:9000)
- [ ] Upload bank_statement.csv + daybook.csv
- [ ] Verify all 21 pipelines run
- [ ] Verify all 22 output files generated
- [ ] Test download (individual files)
- [ ] Test download (ZIP bundle)
- [ ] Fix any bugs found
- [ ] Deploy to Deplexo

---

## 🟢 PRIORITY 7: Marketing (No Talking Needed)

- [ ] Record 1 screen recording (2 min, no face, no voice)
  - [ ] Show bank reconciliation in action
  - [ ] Show 96% match rate
  - [ ] Show 21 pipelines running
  - [ ] Text overlay explaining features
- [ ] Post on LinkedIn
- [ ] Post on Twitter/X
- [ ] Join 3 CA WhatsApp groups (CAclubindia, TaxGuru)
- [ ] Write blog post: "How AI does bank reconciliation in 30 seconds"
- [ ] Write blog post: "50 hours → 3 minutes: AI bookkeeping for CAs"
- [ ] SEO keywords: "bank reconciliation software India"

---

## 🟢 PRIORITY 8: International Expansion

### Phase 1: UAE / Dubai (Month 1-2)
- [ ] Change GST → VAT in UI
- [ ] Change ₹ → AED pricing
- [ ] Add UAE bank formats
- [ ] Marketing: "AI Reconciliation for UAE CAs"
- [ ] Target: 5 UAE CAs

### Phase 2: UK (Month 3-4)
- [ ] Add VAT reconciliation (UK MTD)
- [ ] UK bank formats (Barclays, HSBC, Lloyds)
- [ ] £ pricing (£6/use)
- [ ] Open Banking API integration
- [ ] Target: 10 UK CAs

### Phase 3: USA (Month 5-8)
- [ ] Sales tax reconciliation (50 states)
- [ ] US bank formats (Chase, BofA, Wells Fargo)
- [ ] $ pricing ($9/use)
- [ ] Stripe integration
- [ ] SOC 2 compliance
- [ ] 1099/W-2 reconciliation
- [ ] Target: 25 US accountants

---

## 🌍 FUTURE: BorderLedger — Cross-Border Payment Reconciliation

### Product Concept (For Future Reference)
- **Working Name:** BorderLedger (proposed, not built yet)
- **Positioning:** One reconciliation workspace for international trade payments, foreign exchange, transaction fees, and settlement discrepancies
- **Target:** Indian exporters, importers, CA firms, international payment providers, SaaS companies receiving international payments
- **Domain:** globpay.ai (proposed)

### The Problem We Will Solve
- Indian exporter invoices €10,000 to German customer
- Payment goes through: Invoice → Provider Conversion → Fees → Settlement
- Track: €10,000 → ₹9,48,000 (expected) → ₹9,42,000 (actual) → ₹6,000 difference
- Explain difference: provider fees, FX rate, intermediary charges, timing, partial payment, or unresolved discrepancy
- **IMPORTANT:** Do NOT label every difference as loss/fraud

### 5-Stage Reconciliation Chain
1. **Invoice Amount** — Export invoice (€10,000)
2. **Provider Conversion** — Payment provider (Wise, PayPal, Stripe, SWIFT)
3. **Fees & FX Adjustments** — Provider fees, intermediary charges, FX margin
4. **Expected Settlement** — Calculated expected INR credit
5. **Actual Bank Credit** — Actual amount in Indian bank statement

### Input Files (4 files)
1. Export/Import Invoice Register (CSV/Excel)
2. Payment Provider Export (Wise, PayPal, Stripe, SWIFT CSV)
3. Indian Bank Statement (CSV)
4. FX Rate Record (optional — RBI rates)

### Discrepancy Categories (8 types)
- ✅ Matched (fully reconciled)
- 📊 FX Rate Difference (normal, expected)
- 💰 Provider Fee (documented cost)
- 🏦 Intermediary Bank Charge (SWIFT fee)
- ⏰ Timing Difference (not yet settled)
- 📦 Partial Payment (invoice not fully paid)
- 🔄 Reversed/Refunded
- ⚠️ Unexplained Discrepancy (needs review)

### Multi-Currency Support (Phase 1)
- 🇪🇺 EUR, 🇺🇸 USD, 🇬🇧 GBP, 🇦🇪 AED
- Auto-detect currency from file
- FX rate sources: RBI reference rate, provider actual rate, interbank rate

### Pricing Plan
- **Free Tier:** 1 free cross-border reconciliation/month (summary only)
- **Standard:** ₹999/reconciliation (full chain, 3 currencies, CSV report)
- **Premium:** ₹1,999/reconciliation (unlimited currencies, FX comparison, FEMA/eBRC, audit trail)
- **Enterprise:** ₹4,999/month (unlimited, multi-client, API, custom integrations)

### Development Phases
- **Phase 1 (MVP — 2-3 days):** New tab "🌍 Cross-Border", 4 file upload, basic matching, single currency (EUR→INR), CSV report
- **Phase 2 (Full — 1 week):** Multi-currency, FX rate comparison, fee breakdown, 8 discrepancy types, chain visualization
- **Phase 3 (Compliance — 2 weeks):** FEMA checks, eBRC matching, export benefits tracking, GST export zero-rating, audit trail
- **Phase 4 (Future):** CBDC integration, SWIFT GPI tracking, real-time rate API, API for providers, white-label

### Technical Fit (Reuse Existing Infrastructure)
- Upload system (extend for 4 files)
- SmartFileParser (auto-detect columns)
- ML matching engine (extend for multi-currency)
- Auth, Payment, History, Clients, Free Tier, Toast, Progress Bar, Mobile Responsive
- **NEW:** Currency converter, FX analyzer, chain matcher, fee categorizer, settlement tracker, FEMA/eBRC checker, CBDC placeholder

### Decision: Build as New Tab in ReconcileAI First
- ✅ Reuses ALL existing infrastructure
- ✅ Same users (CAs do export work)
- ✅ Fastest to build (2-3 days MVP)
- ✅ Test market before separate product
- ✅ Can split later if it grows
- **Don't build separate product yet** — duplicate infra = 2-4 weeks vs 2-3 days

### Open Questions (When We Build)
1. Which currencies first? (EUR, USD, GBP?)
2. Which payment providers? (Wise, PayPal, Stripe, SWIFT?)
3. MVP scope: Just matching + discrepancy? Or FX analysis too?
4. Pricing: ₹999? ₹1,999? Or different?
5. Include eBRC/FEMA compliance in MVP or later?

---

## 📋 ALL COMPLETED TASKS (Reference)

### Core Services (All Deployed)
- [x] Bank Reconciliation (BRS) — ₹499
- [x] GST Reconciliation — ₹499
- [x] GSTR-1 Preparation & Filing — ₹499
- [x] GSTR-2B Reconciliation — ₹499
- [x] GSTR-3B Preparation & Filing — ₹499
- [x] Complete Bookkeeping (21 pipelines) — ₹2,999
- [x] UPI Reconciliation — ₹499

### Infrastructure (All Deployed)
- [x] ML model trained on real data (security company)
- [x] SmartFileParser (any file format)
- [x] ReconciliationEngine (95%+ accuracy)
- [x] GST filing via ClearTax API
- [x] Payment system (Razorpay UPI)
- [x] Backend deployed on Deplexo
- [x] Frontend deployed on Deplexo
- [x] Bookkeeping tab + API + progress bar
- [x] GitHub repo setup + auto-deploy

### App Features (All Deployed — 12 October 2026)
- [x] Error Handling → Toast notifications (replace alert())
- [x] Mobile Responsive → CSS media queries (tablet + phone + touch)
- [x] Progress Feedback → Progress bar (bookkeeping 21 pipelines)
- [x] Settings & Preferences → Auto-fill GSTIN, period, business name
- [x] Reconciliation History → PostgreSQL + save/view/delete past work
- [x] Client Management → Full CRUD (add/edit/delete/search)
- [x] Free Tier → 2 BRS + 1 GST + 1 UPI free/month + paywall
- [x] Homepage Update → Pricing cards + features + free tier banner

### Planning (All Decided)
- [x] App improvement plan (API vs Build decision)
- [x] Tally Connector architecture plan
- [x] Self-Learning model architecture plan
- [x] Domain name decision (reconcileai.in)
- [x] Free tier strategy decided
- [x] International expansion plan
- [x] BorderLedger / Cross-Border plan (future reference)
- [x] First CA outreach (CA Kiran Dubey — LinkedIn)

---

## 📊 REVENUE PLAN

| Service | Price | Target Customers | Monthly Revenue |
|---------|-------|-----------------|-----------------|
| Bank Reconciliation | ₹499 | 100 | ₹49,900 |
| GST Reconciliation | ₹499 | 80 | ₹39,920 |
| GSTR-1/2B/3B | ₹499 each | 50 each | ₹74,850 |
| Bookkeeping | ₹2,999 | 20 | ₹59,980 |
| UPI Reconciliation | ₹499 | 30 | ₹14,970 |
| Tally Push (+₹300) | +₹300 | 60 | ₹18,000 |
| Security Audit | ₹4,999 | 5 | ₹24,995 |
| **TOTAL** | | **395** | **₹2,82,615** |

| Month | Target Customers | Revenue |
|-------|-----------------|---------|
| Month 1 | 5 | ₹2,500 |
| Month 3 | 25 | ₹12,500 |
| Month 6 | 100 | ₹50,000 |
| Month 12 | 500 | ₹2,50,000 |

---

## 🎯 KEY DECISIONS MADE

1. **Name:** ReconcileAI (NOT freereconcileai)
2. **Domain:** reconcileai.in + reconcileai.com
3. **Free Tier:** 2 BRS + 1 GST + 1 UPI free/month (backend + frontend)
4. **Hosting:** Deplexo Pro ($10/month)
5. **ML Model:** Real data trained (security company)
6. **Self-Learning:** Pattern memory + feedback loop
7. **Tally:** Local Agent (first) + TDL Plugin (later)
8. **Pricing:** Per-use (₹499) + Tally Push (+₹300) + Bookkeeping (₹2,999)
9. **Expansion:** India → UAE → UK → USA
10. **Marketing:** Content + SEO + Free Tier (no talking)
11. **Login:** Firebase Auth (not custom)
12. **Email:** Gmail SMTP → SendGrid
13. **Approach:** Build locally first, then deploy
14. **Database:** PostgreSQL (Aiven) for all tables
15. **Free Tier Enforcement:** Frontend (localStorage) + Backend (PostgreSQL)
16. **BorderLedger:** Future product — Cross-Border Payment Reconciliation (new tab in ReconcileAI first)
17. **Paywall:** Summary free, full report ₹499 behind paywall

---

## 📞 CONTACTS & ACCOUNTS

- **GitHub:** (repo URL)
- **Deplexo:** reconcileai.deplexo.com
- **Cloudflare:** (domain registrar)
- **ClearTax API:** (GST filing)
- **Razorpay:** (payments)
- **Aiven PostgreSQL:** (database)
- **First CA Contact:** CA Kiran Dubey (LinkedIn, no reply)

---

# END OF PENDING TASKS
# Review this file weekly
# Update checkboxes as tasks complete
# Last Updated: 12 October 2026
