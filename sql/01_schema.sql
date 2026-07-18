-- Core tables for clinical trials data

CREATE TABLE IF NOT EXISTS trials (
    nct_id                  VARCHAR(20) PRIMARY KEY,
    brief_title             TEXT,
    official_title          TEXT,
    overall_status          VARCHAR(50),
    study_type              VARCHAR(50),
    sponsor_name            TEXT,
    sponsor_class           VARCHAR(50),
    start_date              DATE,
    primary_completion_date DATE,
    completion_date         DATE,
    enrollment_count        INTEGER,
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS trial_conditions (
    id        SERIAL PRIMARY KEY,
    nct_id    VARCHAR(20) REFERENCES trials(nct_id) ON DELETE CASCADE,
    condition TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS trial_phases (
    id     SERIAL PRIMARY KEY,
    nct_id VARCHAR(20) REFERENCES trials(nct_id) ON DELETE CASCADE,
    phase  VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS trial_locations (
    id      SERIAL PRIMARY KEY,
    nct_id  VARCHAR(20) REFERENCES trials(nct_id) ON DELETE CASCADE,
    country VARCHAR(100) NOT NULL,
    city    VARCHAR(100),
    state   VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_trials_status ON trials(overall_status);
CREATE INDEX IF NOT EXISTS idx_trials_sponsor_class ON trials(sponsor_class);
CREATE INDEX IF NOT EXISTS idx_trial_conditions_condition ON trial_conditions(condition);
CREATE INDEX IF NOT EXISTS idx_trial_phases_phase ON trial_phases(phase);
CREATE INDEX IF NOT EXISTS idx_trial_locations_country ON trial_locations(country);
