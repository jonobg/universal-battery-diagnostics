-- Enhanced Universal Battery Diagnostics Framework Database Schema
-- Advanced schema with environmental monitoring, test scenarios, and analytics
-- Based on handtool_batteries research and professional requirements

-- Core battery inventory
CREATE TABLE IF NOT EXISTS batteries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    one_key_id TEXT UNIQUE,                    -- Manufacturer battery ID (e.g., Milwaukee ONE-KEY)
    serial_number TEXT,                        -- Physical serial number
    model TEXT NOT NULL,                       -- Battery model (BL1830B, DCB606, etc.)
    manufacturer TEXT NOT NULL,                -- Milwaukee, Makita, DeWalt, Ryobi
    platform TEXT,                            -- M18, LXT, 20V MAX XR, ONE+
    nominal_voltage_v REAL NOT NULL,           -- 18V, 20V, 40V
    nominal_capacity_ah REAL NOT NULL,         -- 2.0Ah, 5.0Ah, 9.0Ah
    chemistry TEXT DEFAULT 'Li-ion',           -- Li-ion, LiFePO4, etc.
    cell_count INTEGER,                        -- Number of cells in series
    cell_configuration TEXT,                   -- "5S1P", "10S2P", etc.
    manufacture_date DATE,                     -- When battery was made
    purchase_date DATE,                        -- When user acquired it
    purchase_price REAL,                      -- Cost for ROI analysis
    warranty_months INTEGER DEFAULT 36,        -- Warranty period
    initial_capacity_ah REAL,                 -- Factory capacity rating
    first_use_date DATE,                      -- When battery was first used
    location TEXT,                            -- Storage/usage location
    owner_notes TEXT,                         -- User-defined notes
    fleet_identifier TEXT,                    -- For commercial fleet tracking
    is_active BOOLEAN DEFAULT 1,              -- Still in use
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Diagnostic sessions (each time battery is analyzed)
CREATE TABLE IF NOT EXISTS diagnostic_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battery_id INTEGER NOT NULL,
    session_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_type TEXT DEFAULT 'standard',      -- standard, quick, comprehensive, warranty
    protocol_version TEXT,                     -- Protocol version used
    firmware_version TEXT,                     -- Battery firmware if available
    hardware_interface TEXT,                  -- UART adapter, protocol analyzer
    operator TEXT,                            -- Who performed the diagnostic
    session_duration_seconds INTEGER,         -- How long diagnostic took
    data_completeness_percent REAL,           -- % of expected data received
    communication_errors INTEGER DEFAULT 0,    -- Protocol errors during session
    success BOOLEAN NOT NULL,                  -- Did session complete successfully
    failure_reason TEXT,                      -- Why session failed
    environmental_notes TEXT,                 -- Temperature, humidity, conditions
    battery_state_before TEXT,                -- charged, empty, hot, cold, rested
    battery_state_after TEXT,                 -- charged, empty, hot, cold, rested
    quality_rating INTEGER CHECK(quality_rating >= 1 AND quality_rating <= 5),
    notes TEXT,                               -- Session-specific observations
    FOREIGN KEY (battery_id) REFERENCES batteries(id) ON DELETE CASCADE
);

-- Raw register data (exactly as received from battery)
CREATE TABLE IF NOT EXISTS raw_register_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    register_address TEXT NOT NULL,            -- Register identifier (hex or name)
    raw_value_hex TEXT NOT NULL,              -- Exact hex data received
    raw_value_bytes BLOB,                     -- Binary data
    timestamp_ms INTEGER,                     -- Milliseconds since session start
    checksum_valid BOOLEAN,                   -- Did checksum validate
    read_attempt INTEGER DEFAULT 1,           -- Which attempt (for retries)
    protocol_notes TEXT,                      -- Protocol-specific metadata
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(id) ON DELETE CASCADE
);

-- Parsed register values (human-readable interpretations)
CREATE TABLE IF NOT EXISTS parsed_register_values (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    register_address TEXT NOT NULL,           -- Same as raw_register_data
    register_name TEXT,                       -- Human-readable name
    parsed_value REAL,                       -- Numeric interpretation
    parsed_value_text TEXT,                  -- Text interpretation
    units TEXT,                              -- mV, mAh, %, °C, etc.
    data_type TEXT,                          -- voltage, current, temperature, count
    confidence_level TEXT,                   -- high, medium, low, unknown
    parsing_method TEXT,                     -- how value was interpreted
    validation_status TEXT,                  -- validated, suspect, error
    notes TEXT,                              -- Parsing-specific notes
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(id) ON DELETE CASCADE
);

-- Health metrics and calculated values
CREATE TABLE IF NOT EXISTS health_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    capacity_percentage INTEGER,              -- % of original capacity
    health_score INTEGER,                     -- Overall health 0-100
    cycle_count INTEGER,                      -- Charge cycles completed
    internal_resistance_mohm REAL,           -- Internal resistance
    cell_imbalance_mv INTEGER,               -- Max voltage difference between cells
    self_discharge_rate_percent REAL,        -- % discharge per month when idle
    charge_efficiency_percent REAL,          -- Charging efficiency
    discharge_efficiency_percent REAL,       -- Discharge efficiency
    temperature_during_test_c REAL,          -- Battery temperature during test
    voltage_sag_under_load_v REAL,           -- Voltage drop under high load
    recovery_time_seconds INTEGER,           -- Time to stabilize after load
    power_capability_w REAL,                 -- Maximum sustainable power output
    energy_density_wh_kg REAL,               -- Energy per unit weight
    predicted_remaining_cycles INTEGER,       -- Machine learning prediction
    degradation_rate_percent_per_100cycles REAL, -- Rate of capacity loss
    thermal_stability_rating TEXT,           -- excellent, good, poor, concerning
    safety_status TEXT,                      -- safe, monitor, warning, critical
    warranty_status TEXT,                    -- valid, expired, voided, claim_eligible
    calculated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(id) ON DELETE CASCADE
);

-- Individual cell voltage monitoring
CREATE TABLE IF NOT EXISTS cell_voltages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    cell_number INTEGER NOT NULL,             -- 1, 2, 3, 4, 5 for 5S pack
    voltage_mv INTEGER NOT NULL,              -- Cell voltage in millivolts
    voltage_rank INTEGER,                     -- 1=highest, 5=lowest for 5S
    deviation_from_average_mv INTEGER,        -- How far from pack average
    is_lowest_cell BOOLEAN DEFAULT 0,         -- Is this the weakest cell?
    is_highest_cell BOOLEAN DEFAULT 0,        -- Is this the strongest cell?
    historical_consistency TEXT,             -- always_low, always_high, variable
    degradation_indicator BOOLEAN DEFAULT 0,  -- Is this cell showing wear?
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(id) ON DELETE CASCADE
);

-- Discharge histogram data (current usage patterns)
CREATE TABLE IF NOT EXISTS discharge_histograms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    current_range_start_a REAL NOT NULL,      -- 0, 25, 50, 75, 100, 125A
    current_range_end_a REAL NOT NULL,        -- 25, 50, 75, 100, 125, 150A
    time_spent_seconds INTEGER NOT NULL,      -- Time in this current range
    percentage_of_total_use REAL,            -- % of battery's lifetime in this range
    cumulative_energy_wh REAL,               -- Total energy delivered in this range
    average_efficiency_percent REAL,         -- Efficiency in this current range
    thermal_impact_rating TEXT,              -- low, medium, high impact on battery temp
    stress_level TEXT,                       -- easy, moderate, hard, extreme on battery
    real_world_equivalent TEXT,              -- drill, grinder, saw, idle
    FOREIGN KEY (session_id) REFERENCES diagnostic_sessions(id) ON DELETE CASCADE
);

-- Battery comparisons and fleet analysis
CREATE TABLE IF NOT EXISTS battery_comparisons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    comparison_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comparison_type TEXT NOT NULL,           -- peer_group, historical, warranty_baseline
    primary_battery_id INTEGER NOT NULL,     -- Battery being compared
    reference_group TEXT,                    -- "same_model_same_age", "warranty_database"
    sample_size INTEGER,                     -- How many batteries in comparison
    primary_capacity_percentage INTEGER,     -- This battery's capacity
    reference_avg_capacity_percentage REAL,  -- Average of comparison group
    capacity_percentile INTEGER,            -- Where this battery ranks (1-100)
    primary_health_score INTEGER,           -- This battery's health score
    reference_avg_health_score REAL,        -- Average health of comparison group
    health_percentile INTEGER,              -- Health ranking (1-100)
    primary_cycle_count INTEGER,            -- This battery's cycles
    reference_avg_cycle_count REAL,         -- Average cycles of comparison group
    cycle_percentile INTEGER,               -- Cycle count ranking
    performance_category TEXT,              -- excellent, above_average, average, below_average, poor
    outlier_status TEXT,                    -- normal, positive_outlier, negative_outlier
    statistical_confidence REAL,            -- How confident is this comparison (0-1)
    actionable_insights TEXT,               -- What user should do based on comparison
    warranty_implications TEXT,             -- Warranty status based on peer comparison
    FOREIGN KEY (primary_battery_id) REFERENCES batteries(id) ON DELETE CASCADE
);

-- Community data sharing and aggregation
CREATE TABLE IF NOT EXISTS community_submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    battery_model TEXT NOT NULL,            -- Anonymized model info
    battery_age_months INTEGER,             -- Age when submitted
    cycle_count INTEGER,                    -- Cycles at time of submission
    capacity_percentage INTEGER,            -- Remaining capacity
    health_score INTEGER,                   -- Calculated health score
    usage_pattern TEXT,                     -- professional, hobbyist, light_use, heavy_use
    climate_zone TEXT,                      -- tropical, temperate, cold, desert
    storage_conditions TEXT,               -- garage, heated, outdoor, climate_controlled
    submission_hash TEXT UNIQUE,           -- Anonymous identifier
    data_quality_score INTEGER,            -- Reliability of submitted data
    validation_status TEXT,                -- verified, pending, rejected
    contribution_value TEXT,               -- high, medium, low value to community
    geographic_region TEXT,                -- North America, Europe, Asia, etc.
    user_consent_level TEXT,               -- full_sharing, anonymized_only, metadata_only
);

-- Time-series monitoring for long-term tracking
CREATE TABLE IF NOT EXISTS monitoring_sessions (
    session_id TEXT PRIMARY KEY,            -- UUID for monitoring session
    battery_id INTEGER NOT NULL,
    start_timestamp TIMESTAMP NOT NULL,
    end_timestamp TIMESTAMP,
    monitoring_type TEXT NOT NULL,          -- idle_tracking, usage_monitoring, charging_analysis
    sample_interval_seconds INTEGER NOT NULL, -- How often data was collected
    total_samples INTEGER,                  -- Number of data points collected
    monitoring_trigger TEXT,               -- scheduled, event_driven, user_initiated
    monitoring_location TEXT,              -- where battery was during monitoring
    environmental_controlled BOOLEAN,       -- Was environment controlled?
    data_completeness_percent REAL,        -- % of expected samples received
    anomalies_detected INTEGER,            -- Number of unusual readings
    session_quality TEXT,                  -- excellent, good, fair, poor
    insights_generated TEXT,               -- Key findings from this monitoring
    follow_up_recommended BOOLEAN DEFAULT 0, -- Should this battery be monitored again?
    FOREIGN KEY (battery_id) REFERENCES batteries(id) ON DELETE CASCADE
);

-- Time-series data points
CREATE TABLE IF NOT EXISTS time_series_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    monitoring_session_id TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    voltage_mv INTEGER,                     -- Pack voltage
    current_ma INTEGER,                     -- Current draw (+ discharge, - charge)
    temperature_c REAL,                     -- Battery temperature
    state_of_charge_percent INTEGER,        -- SOC if available
    power_w REAL,                          -- Instantaneous power
    cumulative_energy_wh REAL,             -- Energy since monitoring started
    event_marker TEXT,                     -- charging_start, load_applied, etc.
    data_quality TEXT,                     -- good, interpolated, estimated, error
    FOREIGN KEY (monitoring_session_id) REFERENCES monitoring_sessions(session_id) ON DELETE CASCADE
);

-- Register change events (significant changes over time)
CREATE TABLE IF NOT EXISTS register_change_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    battery_id INTEGER NOT NULL,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    register_address TEXT NOT NULL,
    previous_value TEXT,                    -- Value before change
    new_value TEXT NOT NULL,               -- Value after change
    change_magnitude REAL,                 -- How big was the change
    change_type TEXT,                      -- gradual_drift, sudden_jump, periodic, anomaly
    significance_level TEXT,               -- critical, high, medium, low, normal
    potential_causes TEXT,                 -- What might have caused this change
    impact_assessment TEXT,                -- How this affects battery performance
    recommendation TEXT,                   -- What user should do about it
    automated_detection BOOLEAN DEFAULT 0,  -- Was this auto-detected?
    human_verified BOOLEAN DEFAULT 0,      -- Has a human confirmed this is significant?
    follow_up_required BOOLEAN DEFAULT 0,  -- Does this need investigation?
    notes TEXT,
    FOREIGN KEY (battery_id) REFERENCES batteries(id) ON DELETE CASCADE
);

-- Performance indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_batteries_model_manufacturer ON batteries(model, manufacturer);
CREATE INDEX IF NOT EXISTS idx_batteries_active_platform ON batteries(is_active, platform);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_battery_date ON diagnostic_sessions(battery_id, session_date);
CREATE INDEX IF NOT EXISTS idx_diagnostic_sessions_success ON diagnostic_sessions(success, session_date);
CREATE INDEX IF NOT EXISTS idx_raw_register_data_session_register ON raw_register_data(session_id, register_address);
CREATE INDEX IF NOT EXISTS idx_parsed_register_values_session_register ON parsed_register_values(session_id, register_address);
CREATE INDEX IF NOT EXISTS idx_health_metrics_session ON health_metrics(session_id);
CREATE INDEX IF NOT EXISTS idx_health_metrics_capacity ON health_metrics(capacity_percentage, health_score);
CREATE INDEX IF NOT EXISTS idx_cell_voltages_session_cell ON cell_voltages(session_id, cell_number);
CREATE INDEX IF NOT EXISTS idx_discharge_histograms_session ON discharge_histograms(session_id);
CREATE INDEX IF NOT EXISTS idx_battery_comparisons_battery ON battery_comparisons(primary_battery_id, comparison_date);
CREATE INDEX IF NOT EXISTS idx_community_submissions_model ON community_submissions(battery_model, submission_date);
CREATE INDEX IF NOT EXISTS idx_monitoring_sessions_battery ON monitoring_sessions(battery_id, start_timestamp);
CREATE INDEX IF NOT EXISTS idx_time_series_data_session_time ON time_series_data(monitoring_session_id, timestamp);
CREATE INDEX IF NOT EXISTS idx_register_change_events_battery_time ON register_change_events(battery_id, event_timestamp);

-- Views for common analytical queries
CREATE VIEW IF NOT EXISTS battery_health_summary AS
SELECT 
    b.id,
    b.one_key_id,
    b.model,
    b.manufacturer,
    b.platform,
    b.nominal_capacity_ah,
    b.purchase_date,
    julianday('now') - julianday(b.purchase_date) as age_days,
    ds.session_date as last_diagnostic_date,
    hm.capacity_percentage,
    hm.health_score,
    hm.cycle_count,
    hm.internal_resistance_mohm,
    hm.cell_imbalance_mv,
    hm.safety_status,
    hm.warranty_status,
    CASE 
        WHEN hm.capacity_percentage >= 80 THEN 'excellent'
        WHEN hm.capacity_percentage >= 70 THEN 'good'
        WHEN hm.capacity_percentage >= 60 THEN 'fair'
        WHEN hm.capacity_percentage >= 50 THEN 'poor'
        ELSE 'critical'
    END as capacity_rating,
    CASE
        WHEN hm.health_score >= 90 THEN 'excellent'
        WHEN hm.health_score >= 75 THEN 'good'
        WHEN hm.health_score >= 60 THEN 'fair'
        WHEN hm.health_score >= 40 THEN 'poor'
        ELSE 'critical'
    END as health_rating
FROM batteries b
LEFT JOIN diagnostic_sessions ds ON b.id = ds.battery_id 
    AND ds.session_date = (
        SELECT MAX(session_date) 
        FROM diagnostic_sessions ds2 
        WHERE ds2.battery_id = b.id AND ds2.success = 1
    )
LEFT JOIN health_metrics hm ON ds.id = hm.session_id
WHERE b.is_active = 1;

CREATE VIEW IF NOT EXISTS fleet_performance_overview AS
SELECT 
    manufacturer,
    platform,
    model,
    COUNT(*) as battery_count,
    AVG(capacity_percentage) as avg_capacity,
    AVG(health_score) as avg_health_score,
    AVG(cycle_count) as avg_cycles,
    MIN(capacity_percentage) as min_capacity,
    MAX(capacity_percentage) as max_capacity,
    COUNT(CASE WHEN capacity_rating = 'excellent' THEN 1 END) as excellent_count,
    COUNT(CASE WHEN capacity_rating = 'good' THEN 1 END) as good_count,
    COUNT(CASE WHEN capacity_rating = 'fair' THEN 1 END) as fair_count,
    COUNT(CASE WHEN capacity_rating = 'poor' THEN 1 END) as poor_count,
    COUNT(CASE WHEN capacity_rating = 'critical' THEN 1 END) as critical_count
FROM battery_health_summary
GROUP BY manufacturer, platform, model
ORDER BY manufacturer, platform, avg_capacity DESC;

CREATE VIEW IF NOT EXISTS warranty_analysis AS
SELECT 
    b.id,
    b.model,
    b.manufacturer,
    b.purchase_date,
    b.warranty_months,
    julianday('now') - julianday(b.purchase_date) as age_days,
    (julianday('now') - julianday(b.purchase_date)) / 30.0 as age_months,
    b.warranty_months - ((julianday('now') - julianday(b.purchase_date)) / 30.0) as warranty_remaining_months,
    hm.capacity_percentage,
    hm.health_score,
    hm.cycle_count,
    hm.warranty_status,
    CASE 
        WHEN (julianday('now') - julianday(b.purchase_date)) / 30.0 > b.warranty_months THEN 'expired'
        WHEN hm.capacity_percentage < 60 AND (julianday('now') - julianday(b.purchase_date)) / 30.0 <= b.warranty_months THEN 'potential_claim'
        WHEN (julianday('now') - julianday(b.purchase_date)) / 30.0 <= b.warranty_months THEN 'covered'
        ELSE 'unknown'
    END as warranty_claim_status
FROM batteries b
LEFT JOIN diagnostic_sessions ds ON b.id = ds.battery_id 
    AND ds.session_date = (
        SELECT MAX(session_date) 
        FROM diagnostic_sessions ds2 
        WHERE ds2.battery_id = b.id AND ds2.success = 1
    )
LEFT JOIN health_metrics hm ON ds.id = hm.session_id
WHERE b.is_active = 1;