-- ReconcileAI Price Update Migration
-- ₹499 → ₹299 and ₹9,999 → ₹5,999

-- 1. Update pricing/plan table (if exists)
UPDATE plans SET price = 299 WHERE price = 499;
UPDATE plans SET price = 5999 WHERE price = 9999;

-- 2. Update subscriptions table (if exists)
UPDATE subscriptions SET plan_price = 299 WHERE plan_price = 499;
UPDATE subscriptions SET plan_price = 5999 WHERE plan_price = 9999;

-- 3. Update payments table (if exists)
UPDATE payments SET amount = 299 WHERE amount = 499;
UPDATE payments SET amount = 5999 WHERE amount = 9999;

-- 4. Update any pricing config tables
UPDATE config SET value = '299' WHERE value = '499' AND key LIKE '%price%';
UPDATE config SET value = '5999' WHERE value = '9999' AND key LIKE '%price%';

-- 5. Update users table (if plan_price is stored)
UPDATE users SET plan_price = 299 WHERE plan_price = 499;
UPDATE users SET plan_price = 5999 WHERE plan_price = 9999;

-- 6. Update service_prices or pricing tables
UPDATE service_prices SET price = 299 WHERE price = 499;
UPDATE service_prices SET price = 5999 WHERE price = 9999;

-- Verify changes
SELECT 'plans' as tbl, price, COUNT(*) FROM plans GROUP BY price;
SELECT 'payments' as tbl, amount, COUNT(*) FROM payments GROUP BY amount;
SELECT 'subscriptions' as tbl, plan_price, COUNT(*) FROM subscriptions GROUP BY plan_price;
