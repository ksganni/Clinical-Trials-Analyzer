-- Analytics views for Tableau / SQL reporting

-- Active recruiting trials by disease area (condition)
CREATE OR REPLACE VIEW v_active_trials_by_condition AS
SELECT
    tc.condition AS disease_area,
    COUNT(DISTINCT t.nct_id) AS active_trial_count
FROM trials t
JOIN trial_conditions tc ON t.nct_id = tc.nct_id
WHERE t.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION', 'ACTIVE_NOT_RECRUITING')
GROUP BY tc.condition
ORDER BY active_trial_count DESC;

-- Completion / success rates by phase
-- "Completed" = COMPLETED status; "Stopped early" = TERMINATED/WITHDRAWN/SUSPENDED
CREATE OR REPLACE VIEW v_completion_rates_by_phase AS
SELECT
    tp.phase,
    COUNT(DISTINCT t.nct_id) AS total_trials,
    COUNT(DISTINCT t.nct_id) FILTER (WHERE t.overall_status = 'COMPLETED') AS completed_trials,
    COUNT(DISTINCT t.nct_id) FILTER (
        WHERE t.overall_status IN ('TERMINATED', 'WITHDRAWN', 'SUSPENDED')
    ) AS stopped_early_trials,
    ROUND(
        100.0 * COUNT(DISTINCT t.nct_id) FILTER (WHERE t.overall_status = 'COMPLETED')
        / NULLIF(COUNT(DISTINCT t.nct_id), 0),
        1
    ) AS completion_rate_pct
FROM trials t
JOIN trial_phases tp ON t.nct_id = tp.nct_id
GROUP BY tp.phase
ORDER BY tp.phase;

-- Geographic distribution of research activity
CREATE OR REPLACE VIEW v_trials_by_country AS
SELECT
    tl.country,
    COUNT(DISTINCT t.nct_id) AS trial_count,
    COUNT(DISTINCT t.nct_id) FILTER (
        WHERE t.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
    ) AS actively_recruiting_count
FROM trials t
JOIN trial_locations tl ON t.nct_id = tl.nct_id
GROUP BY tl.country
ORDER BY trial_count DESC;

-- Trials by sponsor type (INDUSTRY, NIH, OTHER, etc.)
CREATE OR REPLACE VIEW v_trials_by_sponsor_class AS
SELECT
    COALESCE(sponsor_class, 'UNKNOWN') AS sponsor_class,
    COUNT(*) AS trial_count,
    COUNT(*) FILTER (WHERE overall_status = 'COMPLETED') AS completed_count,
    COUNT(*) FILTER (
        WHERE overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
    ) AS recruiting_count
FROM trials
GROUP BY COALESCE(sponsor_class, 'UNKNOWN')
ORDER BY trial_count DESC;

-- Overall status summary (good for KPI cards in Tableau)
CREATE OR REPLACE VIEW v_trial_status_summary AS
SELECT
    overall_status,
    COUNT(*) AS trial_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_total
FROM trials
GROUP BY overall_status
ORDER BY trial_count DESC;

-- Flat export view - one row per trial with primary condition & phase
CREATE OR REPLACE VIEW v_trials_flat AS
SELECT
    t.nct_id,
    t.brief_title,
    t.overall_status,
    t.study_type,
    t.sponsor_name,
    t.sponsor_class,
    t.start_date,
    t.completion_date,
    t.enrollment_count,
    (
        SELECT tc.condition
        FROM trial_conditions tc
        WHERE tc.nct_id = t.nct_id
        LIMIT 1
    ) AS primary_condition,
    (
        SELECT tp.phase
        FROM trial_phases tp
        WHERE tp.nct_id = t.nct_id
        LIMIT 1
    ) AS primary_phase,
    (
        SELECT tl.country
        FROM trial_locations tl
        WHERE tl.nct_id = t.nct_id
        LIMIT 1
    ) AS primary_country
FROM trials t;

-- Interventional vs observational mix
CREATE OR REPLACE VIEW v_trials_by_study_type AS
SELECT
    COALESCE(study_type, 'UNKNOWN') AS study_type,
    COUNT(*) AS trial_count,
    COUNT(*) FILTER (
        WHERE overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
    ) AS recruiting_count,
    ROUND(AVG(enrollment_count) FILTER (WHERE enrollment_count IS NOT NULL), 0) AS avg_enrollment
FROM trials
GROUP BY COALESCE(study_type, 'UNKNOWN')
ORDER BY trial_count DESC;

-- Trial starts over time (timeline / trend chart)
CREATE OR REPLACE VIEW v_trials_started_by_year AS
SELECT
    EXTRACT(YEAR FROM start_date)::INTEGER AS start_year,
    COUNT(*) AS trial_count,
    COUNT(*) FILTER (WHERE overall_status = 'COMPLETED') AS completed_count,
    COUNT(*) FILTER (
        WHERE overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
    ) AS recruiting_count
FROM trials
WHERE start_date IS NOT NULL
GROUP BY EXTRACT(YEAR FROM start_date)
ORDER BY start_year;

-- Average / median enrollment size by phase
CREATE OR REPLACE VIEW v_enrollment_by_phase AS
SELECT
    tp.phase,
    COUNT(DISTINCT t.nct_id) AS trial_count,
    ROUND(AVG(t.enrollment_count) FILTER (WHERE t.enrollment_count IS NOT NULL), 0) AS avg_enrollment,
    (
        SELECT ROUND(
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t2.enrollment_count)::NUMERIC,
            0
        )
        FROM trials t2
        JOIN trial_phases tp2 ON t2.nct_id = tp2.nct_id
        WHERE tp2.phase = tp.phase
          AND t2.enrollment_count IS NOT NULL
    ) AS median_enrollment,
    MAX(t.enrollment_count) AS max_enrollment
FROM trials t
JOIN trial_phases tp ON t.nct_id = tp.nct_id
GROUP BY tp.phase
ORDER BY tp.phase;

-- Top named sponsors (organizations running the most trials)
CREATE OR REPLACE VIEW v_top_sponsors AS
SELECT
    COALESCE(sponsor_name, 'UNKNOWN') AS sponsor_name,
    COALESCE(sponsor_class, 'UNKNOWN') AS sponsor_class,
    COUNT(*) AS trial_count,
    COUNT(*) FILTER (
        WHERE overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
    ) AS recruiting_count,
    COUNT(*) FILTER (WHERE overall_status = 'COMPLETED') AS completed_count
FROM trials
GROUP BY COALESCE(sponsor_name, 'UNKNOWN'), COALESCE(sponsor_class, 'UNKNOWN')
ORDER BY trial_count DESC;

-- Disease area × phase (heatmap: which conditions are studied at which phases)
CREATE OR REPLACE VIEW v_condition_by_phase AS
SELECT
    tc.condition AS disease_area,
    tp.phase,
    COUNT(DISTINCT t.nct_id) AS trial_count
FROM trials t
JOIN trial_conditions tc ON t.nct_id = tc.nct_id
JOIN trial_phases tp ON t.nct_id = tp.nct_id
GROUP BY tc.condition, tp.phase
ORDER BY trial_count DESC;

-- Recruiting pipeline by phase (how many open trials at each phase)
CREATE OR REPLACE VIEW v_recruiting_by_phase AS
SELECT
    tp.phase,
    COUNT(DISTINCT t.nct_id) AS recruiting_trial_count,
    ROUND(AVG(t.enrollment_count) FILTER (WHERE t.enrollment_count IS NOT NULL), 0) AS avg_target_enrollment
FROM trials t
JOIN trial_phases tp ON t.nct_id = tp.nct_id
WHERE t.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
GROUP BY tp.phase
ORDER BY tp.phase;

-- Top US states by trial site activity
CREATE OR REPLACE VIEW v_trials_by_us_state AS
SELECT
    tl.state,
    COUNT(DISTINCT t.nct_id) AS trial_count,
    COUNT(DISTINCT t.nct_id) FILTER (
        WHERE t.overall_status IN ('RECRUITING', 'ENROLLING_BY_INVITATION')
    ) AS actively_recruiting_count
FROM trials t
JOIN trial_locations tl ON t.nct_id = tl.nct_id
WHERE tl.country IN ('United States', 'USA', 'US')
  AND tl.state IS NOT NULL
  AND TRIM(tl.state) <> ''
GROUP BY tl.state
ORDER BY trial_count DESC;
