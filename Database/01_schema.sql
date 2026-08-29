-- ============================================================
-- SMART RF SPECTRUM MONITORING DATABASE
-- DATABASE SCHEMA
-- PostgreSQL 18
-- ============================================================

CREATE TABLE frequency_bands (
    band_id INT PRIMARY KEY,
    band_name VARCHAR(20) NOT NULL,
    start_frequency_mhz DECIMAL(10,2) NOT NULL,
    end_frequency_mhz DECIMAL(10,2) NOT NULL,
    priority INT NOT NULL
);

CREATE TABLE emitters (
    emitter_id INT PRIMARY KEY,
    emitter_name VARCHAR(50) NOT NULL,
    emitter_type VARCHAR(30) NOT NULL,
    priority INT NOT NULL
);

CREATE TABLE transmissions (
    transmission_id INT PRIMARY KEY,
    emitter_id INT NOT NULL,
    band_id INT NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    signal_strength_dbm DECIMAL(8,2),

    FOREIGN KEY (emitter_id)
        REFERENCES emitters(emitter_id),

    FOREIGN KEY (band_id)
        REFERENCES frequency_bands(band_id),

    CHECK (end_time > start_time)
);

CREATE TABLE scans (
    scan_id INT PRIMARY KEY,
    band_id INT NOT NULL,
    strategy VARCHAR(30) NOT NULL,
    scan_time TIMESTAMP NOT NULL,
    dwell_time_ms INT NOT NULL,

    FOREIGN KEY (band_id)
        REFERENCES frequency_bands(band_id),

    CHECK (strategy IN ('Sequential', 'Random', 'Adaptive'))
);

CREATE TABLE observations (
    observation_id INT PRIMARY KEY,
    scan_id INT NOT NULL,
    band_id INT NOT NULL,
    received_signal BOOLEAN NOT NULL,
    actual_signal BOOLEAN NOT NULL,
    snr_db DECIMAL(8,2),

    FOREIGN KEY (scan_id)
        REFERENCES scans(scan_id),

    FOREIGN KEY (band_id)
        REFERENCES frequency_bands(band_id)
);

CREATE TABLE intercepts (
    intercept_id INT PRIMARY KEY,
    observation_id INT NOT NULL,
    emitter_id INT NOT NULL,
    intercept_time TIMESTAMP NOT NULL,
    time_error_ms DECIMAL(10,2),

    FOREIGN KEY (observation_id)
        REFERENCES observations(observation_id),

    FOREIGN KEY (emitter_id)
        REFERENCES emitters(emitter_id)
);