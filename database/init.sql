-- ============================================================
-- Smart Ration Guardian — PostgreSQL Initialization Script
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- ENUMS
-- ============================================================
DO $$ BEGIN
    CREATE TYPE grain_type_enum AS ENUM ('RICE', 'WHEAT', 'SUGAR', 'OIL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE risk_level_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE complaint_type_enum AS ENUM ('UNDERWEIGHT', 'POOR_QUALITY', 'OVERCHARGING', 'NOT_AVAILABLE', 'OTHER');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE complaint_status_enum AS ENUM ('OPEN', 'UNDER_REVIEW', 'RESOLVED');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE severity_enum AS ENUM ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- ============================================================
-- TABLE: shops
-- ============================================================
CREATE TABLE IF NOT EXISTS shops (
    shop_id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_name           VARCHAR(200) NOT NULL,
    owner_name          VARCHAR(200) NOT NULL,
    location            TEXT NOT NULL,
    district            VARCHAR(100) NOT NULL,
    risk_score          DECIMAL(5,2) DEFAULT 0.0,
    risk_level          risk_level_enum DEFAULT 'LOW',
    password_hash       VARCHAR(255) NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: beneficiaries
-- ============================================================
CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ration_card_number      VARCHAR(50) UNIQUE NOT NULL,
    name                    VARCHAR(200) NOT NULL,
    phone                   VARCHAR(20),
    address                 TEXT,
    family_members          INTEGER DEFAULT 1,
    assigned_shop_id        UUID REFERENCES shops(shop_id) ON DELETE SET NULL,
    monthly_entitlement_kg  DECIMAL(8,2) DEFAULT 25.00,
    password_hash           VARCHAR(255) NOT NULL,
    created_at              TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: stock_inventory
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_inventory (
    inventory_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_id                 UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    grain_type              grain_type_enum NOT NULL,
    stock_received_kg       DECIMAL(10,2) DEFAULT 0.0,
    stock_distributed_kg    DECIMAL(10,2) DEFAULT 0.0,
    remaining_stock_kg      DECIMAL(10,2) GENERATED ALWAYS AS (stock_received_kg - stock_distributed_kg) STORED,
    last_updated            TIMESTAMP DEFAULT NOW(),
    UNIQUE(shop_id, grain_type)
);

-- ============================================================
-- TABLE: transactions
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_id             UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    beneficiary_id      UUID NOT NULL REFERENCES beneficiaries(beneficiary_id) ON DELETE CASCADE,
    grain_type          grain_type_enum NOT NULL,
    quantity_given_kg   DECIMAL(8,2) NOT NULL,
    transaction_date    TIMESTAMP DEFAULT NOW(),
    qr_scan_verified    BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- TABLE: complaints
-- ============================================================
CREATE TABLE IF NOT EXISTS complaints (
    complaint_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    beneficiary_id      UUID NOT NULL REFERENCES beneficiaries(beneficiary_id) ON DELETE CASCADE,
    shop_id             UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    complaint_type      complaint_type_enum NOT NULL,
    description         TEXT,
    status              complaint_status_enum DEFAULT 'OPEN',
    ai_category         VARCHAR(100),
    created_at          TIMESTAMP DEFAULT NOW(),
    resolved_at         TIMESTAMP
);

-- ============================================================
-- TABLE: fraud_alerts
-- ============================================================
CREATE TABLE IF NOT EXISTS fraud_alerts (
    alert_id        UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_id         UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    alert_type      VARCHAR(100) NOT NULL,
    description     TEXT,
    severity        severity_enum DEFAULT 'LOW',
    is_reviewed     BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: stock_predictions
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_predictions (
    prediction_id       UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    shop_id             UUID NOT NULL REFERENCES shops(shop_id) ON DELETE CASCADE,
    grain_type          grain_type_enum NOT NULL,
    predicted_demand_kg DECIMAL(10,2),
    prediction_month    DATE NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLE: officers (government officers)
-- ============================================================
CREATE TABLE IF NOT EXISTS officers (
    officer_id      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            VARCHAR(200) NOT NULL,
    email           VARCHAR(200) UNIQUE NOT NULL,
    district        VARCHAR(100),
    password_hash   VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- SEED DATA
-- ============================================================

-- Shops (password: "shop123" — bcrypt hash placeholder)
INSERT INTO shops (shop_id, shop_name, owner_name, location, district, risk_score, risk_level, password_hash) VALUES
    ('a1b2c3d4-0001-0001-0001-000000000001', 'Ravi Ration Shop',    'Ravi Kumar',   '12, Gandhi Nagar, Chennai',     'Chennai',    35.0, 'LOW',    '$2b$12$dummyhashforseeddatashop001xxxxx'),
    ('a1b2c3d4-0002-0002-0002-000000000002', 'Lakshmi Stores',      'Lakshmi Devi', '45, Nehru Street, Coimbatore',  'Coimbatore', 62.5, 'MEDIUM', '$2b$12$dummyhashforseeddatashop002xxxxx'),
    ('a1b2c3d4-0003-0003-0003-000000000003', 'Murugan Fair Price',  'Murugan S',    '7, Anna Road, Madurai',         'Madurai',    80.2, 'HIGH',   '$2b$12$dummyhashforseeddatashop003xxxxx')
ON CONFLICT (shop_id) DO NOTHING;

-- Beneficiaries (password: "ben123")
INSERT INTO beneficiaries (beneficiary_id, ration_card_number, name, phone, address, family_members, assigned_shop_id, monthly_entitlement_kg, password_hash) VALUES
    ('b0000001-0000-0000-0000-000000000001', 'TN-CHN-001001', 'Arun Selvam',      '9876543201', '3, Rose Street, Chennai',        4, 'a1b2c3d4-0001-0001-0001-000000000001', 20.0, '$2b$12$dummyhashforseeddataben001xxxxx'),
    ('b0000001-0000-0000-0000-000000000002', 'TN-CHN-001002', 'Priya Rajan',      '9876543202', '7, Lotus Avenue, Chennai',       3, 'a1b2c3d4-0001-0001-0001-000000000001', 15.0, '$2b$12$dummyhashforseeddataben002xxxxx'),
    ('b0000001-0000-0000-0000-000000000003', 'TN-CHN-001003', 'Suresh Babu',      '9876543203', '21, MG Road, Chennai',           5, 'a1b2c3d4-0001-0001-0001-000000000001', 25.0, '$2b$12$dummyhashforseeddataben003xxxxx'),
    ('b0000001-0000-0000-0000-000000000004', 'TN-CBE-002001', 'Meena Krishnan',   '9876543204', '8, Sundar Nagar, Coimbatore',    2, 'a1b2c3d4-0002-0002-0002-000000000002', 10.0, '$2b$12$dummyhashforseeddataben004xxxxx'),
    ('b0000001-0000-0000-0000-000000000005', 'TN-CBE-002002', 'Vijay Anand',      '9876543205', '14, Bharathi St, Coimbatore',    6, 'a1b2c3d4-0002-0002-0002-000000000002', 30.0, '$2b$12$dummyhashforseeddataben005xxxxx'),
    ('b0000001-0000-0000-0000-000000000006', 'TN-CBE-002003', 'Kavitha Sundar',   '9876543206', '2, Park Road, Coimbatore',       3, 'a1b2c3d4-0002-0002-0002-000000000002', 15.0, '$2b$12$dummyhashforseeddataben006xxxxx'),
    ('b0000001-0000-0000-0000-000000000007', 'TN-MDU-003001', 'Raja Pandian',     '9876543207', '5, Temple Street, Madurai',      4, 'a1b2c3d4-0003-0003-0003-000000000003', 20.0, '$2b$12$dummyhashforseeddataben007xxxxx'),
    ('b0000001-0000-0000-0000-000000000008', 'TN-MDU-003002', 'Saranya Devi',     '9876543208', '9, West Veli St, Madurai',       5, 'a1b2c3d4-0003-0003-0003-000000000003', 25.0, '$2b$12$dummyhashforseeddataben008xxxxx'),
    ('b0000001-0000-0000-0000-000000000009', 'TN-MDU-003003', 'Mani Kumar',       '9876543209', '33, East Veli St, Madurai',      2, 'a1b2c3d4-0003-0003-0003-000000000003', 10.0, '$2b$12$dummyhashforseeddataben009xxxxx'),
    ('b0000001-0000-0000-0000-000000000010', 'TN-MDU-003004', 'Devi Lakshmanan',  '9876543210', '11, Kochadai, Madurai',          7, 'a1b2c3d4-0003-0003-0003-000000000003', 35.0, '$2b$12$dummyhashforseeddataben010xxxxx')
ON CONFLICT (ration_card_number) DO NOTHING;

-- Stock Inventory
INSERT INTO stock_inventory (shop_id, grain_type, stock_received_kg, stock_distributed_kg) VALUES
    ('a1b2c3d4-0001-0001-0001-000000000001', 'RICE',  500.0, 320.0),
    ('a1b2c3d4-0001-0001-0001-000000000001', 'WHEAT', 200.0, 180.0),
    ('a1b2c3d4-0001-0001-0001-000000000001', 'SUGAR', 100.0,  60.0),
    ('a1b2c3d4-0001-0001-0001-000000000001', 'OIL',    50.0,  30.0),
    ('a1b2c3d4-0002-0002-0002-000000000002', 'RICE',  600.0, 580.0),
    ('a1b2c3d4-0002-0002-0002-000000000002', 'WHEAT', 250.0, 245.0),
    ('a1b2c3d4-0002-0002-0002-000000000002', 'SUGAR', 120.0, 118.0),
    ('a1b2c3d4-0002-0002-0002-000000000002', 'OIL',    60.0,  59.0),
    ('a1b2c3d4-0003-0003-0003-000000000003', 'RICE',  700.0, 300.0),
    ('a1b2c3d4-0003-0003-0003-000000000003', 'WHEAT', 300.0, 100.0),
    ('a1b2c3d4-0003-0003-0003-000000000003', 'SUGAR', 150.0,  50.0),
    ('a1b2c3d4-0003-0003-0003-000000000003', 'OIL',    75.0,  20.0)
ON CONFLICT (shop_id, grain_type) DO NOTHING;

-- Transactions (30 records)
INSERT INTO transactions (shop_id, beneficiary_id, grain_type, quantity_given_kg, transaction_date, qr_scan_verified) VALUES
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000001','RICE', 5.0,'2024-11-05 10:00:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000001','WHEAT',2.5,'2024-11-05 10:05:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000002','RICE', 3.0,'2024-11-06 11:00:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000002','SUGAR',1.0,'2024-11-06 11:05:00',FALSE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000003','RICE', 6.0,'2024-11-07 09:30:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000003','WHEAT',3.0,'2024-11-07 09:35:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000001','OIL',  1.0,'2024-11-08 14:00:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000002','WHEAT',2.0,'2024-11-09 10:00:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000003','SUGAR',1.5,'2024-11-10 11:00:00',TRUE),
    ('a1b2c3d4-0001-0001-0001-000000000001','b0000001-0000-0000-0000-000000000001','RICE', 5.0,'2024-11-11 09:00:00',TRUE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000004','RICE', 2.5,'2024-11-05 10:00:00',TRUE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000004','OIL',  0.5,'2024-11-05 10:10:00',FALSE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000005','RICE', 8.0,'2024-11-06 09:00:00',TRUE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000005','WHEAT',4.0,'2024-11-06 09:10:00',FALSE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000006','RICE', 3.0,'2024-11-07 11:00:00',TRUE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000006','SUGAR',1.0,'2024-11-07 11:05:00',TRUE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000004','WHEAT',2.0,'2024-11-08 10:00:00',FALSE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000005','OIL',  1.5,'2024-11-09 10:00:00',TRUE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000006','WHEAT',2.5,'2024-11-10 11:00:00',FALSE),
    ('a1b2c3d4-0002-0002-0002-000000000002','b0000001-0000-0000-0000-000000000004','RICE', 2.5,'2024-11-11 09:00:00',TRUE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000007','RICE', 1.5,'2024-11-05 10:00:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000007','SUGAR',0.5,'2024-11-05 10:10:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000008','RICE', 2.0,'2024-11-06 09:00:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000008','WHEAT',1.0,'2024-11-06 09:10:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000009','RICE', 1.0,'2024-11-07 11:00:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000009','OIL',  0.5,'2024-11-07 11:05:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000010','RICE', 3.0,'2024-11-08 10:00:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000010','WHEAT',2.0,'2024-11-09 10:00:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000007','SUGAR',1.0,'2024-11-10 11:00:00',FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003','b0000001-0000-0000-0000-000000000008','OIL',  1.0,'2024-11-11 09:00:00',FALSE);

-- Complaints (5 records)
INSERT INTO complaints (beneficiary_id, shop_id, complaint_type, description, status, ai_category) VALUES
    ('b0000001-0000-0000-0000-000000000004','a1b2c3d4-0002-0002-0002-000000000002','UNDERWEIGHT',   'Received only 2 kg rice instead of 2.5 kg as per entitlement.',           'OPEN',         'UNDERWEIGHT'),
    ('b0000001-0000-0000-0000-000000000007','a1b2c3d4-0003-0003-0003-000000000003','OVERCHARGING',  'Shop owner demanded extra money for wheat beyond fixed price.',             'UNDER_REVIEW', 'OVERCHARGING'),
    ('b0000001-0000-0000-0000-000000000008','a1b2c3d4-0003-0003-0003-000000000003','POOR_QUALITY',  'Rice distributed was mixed with stones and impurities.',                   'OPEN',         'POOR_QUALITY'),
    ('b0000001-0000-0000-0000-000000000005','a1b2c3d4-0002-0002-0002-000000000002','NOT_AVAILABLE', 'Shop was closed for 3 days during distribution window without notice.',    'RESOLVED',     'NOT_AVAILABLE'),
    ('b0000001-0000-0000-0000-000000000009','a1b2c3d4-0003-0003-0003-000000000003','UNDERWEIGHT',   'Sugar quantity given was less than allocated. Only 400g instead of 1 kg.', 'OPEN',         'UNDERWEIGHT');

-- Fraud Alerts (2 records)
INSERT INTO fraud_alerts (shop_id, alert_type, description, severity, is_reviewed) VALUES
    ('a1b2c3d4-0002-0002-0002-000000000002', 'STOCK_MISMATCH',       'Distributed stock (580 kg) nearly equals received (600 kg) with very low QR verification rate (30%). Possible ghost transactions.', 'HIGH',     FALSE),
    ('a1b2c3d4-0003-0003-0003-000000000003', 'LOW_DISTRIBUTION',     'Only 300 kg out of 700 kg received rice has been distributed despite 4 registered beneficiaries. Possible diversion to black market.', 'CRITICAL', FALSE);

-- Stock Predictions
INSERT INTO stock_predictions (shop_id, grain_type, predicted_demand_kg, prediction_month) VALUES
    ('a1b2c3d4-0001-0001-0001-000000000001','RICE',  350.0,'2024-12-01'),
    ('a1b2c3d4-0001-0001-0001-000000000001','WHEAT', 190.0,'2024-12-01'),
    ('a1b2c3d4-0002-0002-0002-000000000002','RICE',  590.0,'2024-12-01'),
    ('a1b2c3d4-0002-0002-0002-000000000002','WHEAT', 250.0,'2024-12-01'),
    ('a1b2c3d4-0003-0003-0003-000000000003','RICE',  420.0,'2024-12-01'),
    ('a1b2c3d4-0003-0003-0003-000000000003','WHEAT', 200.0,'2024-12-01');

-- Officers
INSERT INTO officers (name, email, district, password_hash) VALUES
    ('District Officer Ramesh', 'officer@tnration.gov.in', 'Chennai', '$2b$12$dummyhashforseeddataofficerxxxxx');

COMMIT;
