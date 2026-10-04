# ReconcileAI — Pending Tasks
# Last Updated: 28 September 2026
# Status: Build locally first, then deploy to Deplexo

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
- [ ] Create feedback table (SQLite)
- [ ] Build FeedbackCollector class (learning_engine.py)
- [ ] API endpoint: POST /api/feedback
- [ ] Frontend: 👍👎 buttons on match results
- [ ] Store user corrections

### Week 2: Pattern Memory
- [ ] Create patterns table (SQLite)
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

## 🟡 PRIORITY 4: App Improvements (8 Items)

### Use External API
- [ ] User Login → Firebase Auth (30 min, free)
- [ ] Email Reports → Gmail SMTP → SendGrid (free)

### Build Own
- [ ] Client Management → SQLite + FastAPI (add/edit/delete clients)
- [ ] Reconciliation History → Save results, view past work
- [ ] Mobile Responsive → CSS media queries
- [ ] Progress Feedback → Polling + progress bar (bookkeeping)
- [ ] Error Handling → Toast notifications (replace alert())
- [ ] Settings & Preferences → Default GSTIN, period, etc.

---

## 🟡 PRIORITY 5: Free Tier Setup

- [ ] 2 free bank reconciliations/month
- [ ] 1 free GST reconciliation/month
- [ ] Summary results free, full report paid
- [ ] Track usage per user (anonymous or logged-in)
- [ ] Block after limit reached
- [ ] "Start free. No credit card needed." on homepage

---

## 🟡 PRIORITY 6: Tally Connector

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

## 🟡 PRIORITY 7: Security AI Integration

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

## 🟢 PRIORITY 8: Bookkeeping Testing

- [ ] Test bookkeeping tab with real data (localhost:9000)
- [ ] Upload bank_statement.csv + daybook.csv
- [ ] Verify all 21 pipelines run
- [ ] Verify all 22 output files generated
- [ ] Test download (individual files)
- [ ] Test download (ZIP bundle)
- [ ] Fix any bugs found
- [ ] Deploy to Deplexo

---

## 🟢 PRIORITY 9: Marketing (No Talking Needed)

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

## 🟢 PRIORITY 10: International Expansion

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

## 📋 COMPLETED TASKS (Reference)

- [x] Bank Reconciliation (BRS) — ₹499
- [x] GST Reconciliation — ₹499
- [x] GSTR-1 Preparation & Filing — ₹499
- [x] GSTR-2B Reconciliation — ₹499
- [x] GSTR-3B Preparation & Filing — ₹499
- [x] Complete Bookkeeping (21 pipelines) — ₹2,999
- [x] ML model trained on real data (security company)
- [x] SmartFileParser (any file format)
- [x] ReconciliationEngine (95%+ accuracy)
- [x] GST filing via ClearTax API
- [x] Payment system (Razorpay UPI)
- [x] Backend deployed on Deplexo
- [x] Frontend deployed on Deplexo
- [x] Bookkeeping tab added to frontend
- [x] Bookkeeping API built
- [x] GitHub repo setup + auto-deploy
- [x] App improvement plan (API vs Build decision)
- [x] Tally Connector architecture plan
- [x] Self-Learning model architecture plan
- [x] Domain name decision (reconcileai.in)
- [x] Free tier strategy decided
- [x] International expansion plan
- [x] First CA outreach (CA Kiran Dubey — LinkedIn)

---

## 📊 REVENUE PLAN

| Service | Price | Target Customers | Monthly Revenue |
|---------|-------|-----------------|-----------------|
| Bank Reconciliation | ₹499 | 100 | ₹49,900 |
| GST Reconciliation | ₹499 | 80 | ₹39,920 |
| GSTR-1/2B/3B | ₹499 each | 50 each | ₹74,850 |
| Bookkeeping | ₹2,999 | 20 | ₹59,980 |
| Tally Push (+₹300) | +₹300 | 60 | ₹18,000 |
| Security Audit | ₹4,999 | 5 | ₹24,995 |
| **TOTAL** | | **365** | **₹2,67,645** |

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
3. **Free Tier:** 2 free reconciliations/month
4. **Hosting:** Deplexo Pro ($10/month)
5. **ML Model:** Real data trained (security company)
6. **Self-Learning:** Pattern memory + feedback loop
7. **Tally:** Local Agent (first) + TDL Plugin (later)
8. **Pricing:** Per-use (₹499) + Tally Push (+₹300)
9. **Expansion:** India → UAE → UK → USA
10. **Marketing:** Content + SEO + Free Tier (no talking)
11. **Login:** Firebase Auth (not custom)
12. **Email:** Gmail SMTP → SendGrid
13. **Approach:** Build locally first, then deploy

---

## 📞 CONTACTS & ACCOUNTS

- **GitHub:** (repo URL)
- **Deplexo:** reconcileai.deplexo.com
- **Cloudflare:** (domain registrar)
- **ClearTax API:** (GST filing)
- **Razorpay:** (payments)
- **First CA Contact:** CA Kiran Dubey (LinkedIn, no reply)

---

# END OF PENDING TASKS
# Review this file weekly
# Update checkboxes as tasks complete
