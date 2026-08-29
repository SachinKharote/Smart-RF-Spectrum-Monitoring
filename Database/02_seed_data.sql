-- ============================================================
-- SMART RF SPECTRUM MONITORING
-- INITIAL / SEED DATA
-- ============================================================

INSERT INTO frequency_bands
    (band_id, band_name, start_frequency_mhz, end_frequency_mhz, priority)
VALUES
    (1,  'Band 1',  100.00, 105.00, 5),
    (2,  'Band 2',  105.00, 110.00, 4),
    (3,  'Band 3',  110.00, 115.00, 3),
    (4,  'Band 4',  115.00, 120.00, 5),
    (5,  'Band 5',  120.00, 125.00, 2),
    (6,  'Band 6',  125.00, 130.00, 4),
    (7,  'Band 7',  130.00, 135.00, 3),
    (8,  'Band 8',  135.00, 140.00, 5),
    (9,  'Band 9',  140.00, 145.00, 2),
    (10, 'Band 10', 145.00, 150.00, 4);

INSERT INTO emitters
    (emitter_id, emitter_name, emitter_type, priority)
VALUES
    (1, 'Emitter Alpha',   'Fixed',            5),
    (2, 'Emitter Bravo',   'Periodic',         4),
    (3, 'Emitter Charlie', 'Intermittent',     3),
    (4, 'Emitter Delta',   'Frequency Agile',  5),
    (5, 'Emitter Echo',    'Periodic',         2);