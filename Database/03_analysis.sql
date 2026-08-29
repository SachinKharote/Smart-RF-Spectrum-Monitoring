-- ============================================================
-- SMART RF SPECTRUM MONITORING
-- ANALYSIS QUERIES
-- PostgreSQL 18
-- ============================================================


-- ============================================================
-- 1. RECORD COUNTS
-- ============================================================

SELECT 'Frequency Bands' AS table_name, COUNT(*) AS records
FROM frequency_bands

UNION ALL

SELECT 'Emitters', COUNT(*)
FROM emitters

UNION ALL

SELECT 'Transmissions', COUNT(*)
FROM transmissions

UNION ALL

SELECT 'Scans', COUNT(*)
FROM scans

UNION ALL

SELECT 'Observations', COUNT(*)
FROM observations

UNION ALL

SELECT 'Intercepts', COUNT(*)
FROM intercepts;


-- ============================================================
-- 2. SCANS BY STRATEGY
-- ============================================================

SELECT
    strategy,
    COUNT(*) AS total_scans
FROM scans
GROUP BY strategy
ORDER BY strategy;


-- ============================================================
-- 3. DETECTION RATE
-- ============================================================

SELECT
    s.strategy,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
    ) AS actual_signals,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
          AND o.received_signal = TRUE
    ) AS successful_detections,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
          AND o.received_signal = FALSE
    ) AS missed_signals,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE o.actual_signal = TRUE
              AND o.received_signal = TRUE
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE o.actual_signal = TRUE
            ),
            0
        ),
        2
    ) AS detection_rate_percent

FROM scans s

JOIN observations o
    ON s.scan_id = o.scan_id

GROUP BY s.strategy

ORDER BY detection_rate_percent DESC;


-- ============================================================
-- 4. FALSE ALARM RATE
-- ============================================================

SELECT
    s.strategy,

    COUNT(*) FILTER (
        WHERE o.actual_signal = FALSE
          AND o.received_signal = TRUE
    ) AS false_alarms,

    COUNT(*) FILTER (
        WHERE o.actual_signal = FALSE
    ) AS no_signal_observations,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE o.actual_signal = FALSE
              AND o.received_signal = TRUE
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE o.actual_signal = FALSE
            ),
            0
        ),
        2
    ) AS false_alarm_rate_percent

FROM scans s

JOIN observations o
    ON s.scan_id = o.scan_id

GROUP BY s.strategy

ORDER BY false_alarm_rate_percent;


-- ============================================================
-- 5. MISSED SIGNALS BY STRATEGY AND BAND
-- ============================================================

SELECT
    s.strategy,
    o.band_id,
    COUNT(*) AS missed_signals

FROM scans s

JOIN observations o
    ON s.scan_id = o.scan_id

WHERE o.actual_signal = TRUE
  AND o.received_signal = FALSE

GROUP BY
    s.strategy,
    o.band_id

ORDER BY
    s.strategy,
    missed_signals DESC;


-- ============================================================
-- 6. DETECTION RATE BY FREQUENCY BAND
-- ============================================================

SELECT
    o.band_id,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
    ) AS actual_signals,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
          AND o.received_signal = TRUE
    ) AS successful_detections,

    ROUND(
        100.0 *
        COUNT(*) FILTER (
            WHERE o.actual_signal = TRUE
              AND o.received_signal = TRUE
        )
        /
        NULLIF(
            COUNT(*) FILTER (
                WHERE o.actual_signal = TRUE
            ),
            0
        ),
        2
    ) AS detection_rate_percent

FROM observations o

GROUP BY o.band_id

ORDER BY o.band_id;


-- ============================================================
-- 7. AVERAGE INTERCEPTION TIME
-- ============================================================

SELECT
    s.strategy,

    ROUND(
        AVG(
            EXTRACT(
                EPOCH FROM
                (i.intercept_time - t.start_time)
            )::numeric
        ),
        3
    ) AS average_intercept_time_seconds

FROM intercepts i

JOIN observations o
    ON i.observation_id = o.observation_id

JOIN scans s
    ON o.scan_id = s.scan_id

JOIN transmissions t
    ON t.emitter_id = i.emitter_id
   AND t.band_id = o.band_id
   AND i.intercept_time >= t.start_time
   AND i.intercept_time <= t.end_time

GROUP BY s.strategy

ORDER BY average_intercept_time_seconds;


-- ============================================================
-- 8. COMPOSITE REWARD
-- ============================================================

SELECT
    s.strategy,

    SUM(
        CASE
            WHEN o.actual_signal = TRUE
             AND o.received_signal = TRUE
                THEN 10

            WHEN o.actual_signal = FALSE
             AND o.received_signal = TRUE
                THEN -2

            WHEN o.actual_signal = TRUE
             AND o.received_signal = FALSE
                THEN -5

            ELSE 0
        END
    ) AS total_reward

FROM scans s

JOIN observations o
    ON s.scan_id = o.scan_id

GROUP BY s.strategy

ORDER BY total_reward DESC;


-- ============================================================
-- 9. CONFUSION MATRIX
-- ============================================================

SELECT
    s.strategy,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
          AND o.received_signal = TRUE
    ) AS true_positives,

    COUNT(*) FILTER (
        WHERE o.actual_signal = FALSE
          AND o.received_signal = TRUE
    ) AS false_positives,

    COUNT(*) FILTER (
        WHERE o.actual_signal = TRUE
          AND o.received_signal = FALSE
    ) AS false_negatives,

    COUNT(*) FILTER (
        WHERE o.actual_signal = FALSE
          AND o.received_signal = FALSE
    ) AS true_negatives

FROM scans s

JOIN observations o
    ON s.scan_id = o.scan_id

GROUP BY s.strategy;


-- ============================================================
-- 10. FINAL STRATEGY COMPARISON
-- ============================================================

WITH metrics AS (

    SELECT
        s.strategy,

        ROUND(
            100.0 *
            COUNT(*) FILTER (
                WHERE o.actual_signal = TRUE
                  AND o.received_signal = TRUE
            )
            /
            NULLIF(
                COUNT(*) FILTER (
                    WHERE o.actual_signal = TRUE
                ),
                0
            ),
            2
        ) AS detection_rate,

        ROUND(
            100.0 *
            COUNT(*) FILTER (
                WHERE o.actual_signal = FALSE
                  AND o.received_signal = TRUE
            )
            /
            NULLIF(
                COUNT(*) FILTER (
                    WHERE o.actual_signal = FALSE
                ),
                0
            ),
            2
        ) AS false_alarm_rate,

        COUNT(*) FILTER (
            WHERE o.actual_signal = TRUE
              AND o.received_signal = FALSE
        ) AS missed_signals

    FROM scans s

    JOIN observations o
        ON s.scan_id = o.scan_id

    GROUP BY s.strategy
),

interception AS (

    SELECT
        s.strategy,

        ROUND(
            AVG(
                EXTRACT(
                    EPOCH FROM
                    (i.intercept_time - t.start_time)
                )::numeric
            ),
            3
        ) AS average_intercept_time

    FROM intercepts i

    JOIN observations o
        ON i.observation_id = o.observation_id

    JOIN scans s
        ON o.scan_id = s.scan_id

    JOIN transmissions t
        ON t.emitter_id = i.emitter_id
       AND t.band_id = o.band_id
       AND i.intercept_time >= t.start_time
       AND i.intercept_time <= t.end_time

    GROUP BY s.strategy
)

SELECT
    m.strategy,
    m.detection_rate,
    m.false_alarm_rate,
    m.missed_signals,
    i.average_intercept_time

FROM metrics m

LEFT JOIN interception i
    ON m.strategy = i.strategy

ORDER BY m.detection_rate DESC;