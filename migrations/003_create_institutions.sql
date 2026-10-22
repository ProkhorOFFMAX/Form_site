CREATE TABLE IF NOT EXISTS educational_institutions (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(500) NOT NULL,
    short_name VARCHAR(100) NOT NULL,
    type VARCHAR(10) NOT NULL CHECK (type IN ('ГБОУ', 'ГБДОУ', 'ОДОД'))
);

CREATE INDEX IF NOT EXISTS idx_ei_type ON educational_institutions (type);
CREATE INDEX IF NOT EXISTS idx_ei_short_name ON educational_institutions (short_name);