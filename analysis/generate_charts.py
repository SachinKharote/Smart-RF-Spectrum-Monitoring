import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from sqlalchemy import create_engine
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv(
    Path(__file__).resolve().parent.parent / ".env"
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = Path("../output/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# CONNECT TO DATABASE
# ============================================================

connection = psycopg2.connect(**DB_CONFIG)

print("Connected to PostgreSQL.")

connection.close()

password = quote_plus(DB_CONFIG["password"])

engine = create_engine(
    f"postgresql+psycopg2://"
    f"{DB_CONFIG['user']}:{password}@"
    f"{DB_CONFIG['host']}:{DB_CONFIG['port']}/"
    f"{DB_CONFIG['database']}"
)

# ============================================================
# FINAL PERFORMANCE QUERY
# ============================================================

query = """
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
"""

# ============================================================
# LOAD DATA INTO PANDAS
# ============================================================

df = pd.read_sql_query(query, engine)

print("\nPerformance results:")
print(df.to_string(index=False))

# ============================================================
# CHART 1 — DETECTION RATE
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    df["strategy"],
    df["detection_rate"]
)

plt.title("Detection Rate by Scanning Strategy")
plt.xlabel("Scanning Strategy")
plt.ylabel("Detection Rate (%)")
plt.ylim(0, 100)

for index, value in enumerate(df["detection_rate"]):
    plt.text(
        index,
        value + 2,
        f"{value:.2f}%",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "detection_rate.png",
    dpi=300
)

plt.close()

# ============================================================
# CHART 2 — FALSE ALARM RATE
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    df["strategy"],
    df["false_alarm_rate"]
)

plt.title("False Alarm Rate by Scanning Strategy")
plt.xlabel("Scanning Strategy")
plt.ylabel("False Alarm Rate (%)")

for index, value in enumerate(df["false_alarm_rate"]):
    plt.text(
        index,
        value + 0.3,
        f"{value:.2f}%",
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "false_alarm_rate.png",
    dpi=300
)

plt.close()

# ============================================================
# CHART 3 — MISSED SIGNALS
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    df["strategy"],
    df["missed_signals"]
)

plt.title("Missed Signals by Scanning Strategy")
plt.xlabel("Scanning Strategy")
plt.ylabel("Number of Missed Signals")

for index, value in enumerate(df["missed_signals"]):
    plt.text(
        index,
        value + 0.5,
        str(value),
        ha="center"
    )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "missed_signals.png",
    dpi=300
)

plt.close()

# ============================================================
# CHART 4 — AVERAGE INTERCEPTION TIME
# ============================================================

plt.figure(figsize=(8, 5))

plt.bar(
    df["strategy"],
    df["average_intercept_time"]
)

plt.title("Average Interception Time by Strategy")
plt.xlabel("Scanning Strategy")
plt.ylabel("Average Interception Time (seconds)")

for index, value in enumerate(df["average_intercept_time"]):
    if pd.notna(value):
        plt.text(
            index,
            value + 0.1,
            f"{value:.2f}s",
            ha="center"
        )

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "average_interception_time.png",
    dpi=300
)

plt.close()

# ============================================================
# SAVE RESULTS AS CSV
# ============================================================

df.to_csv(
    "../output/final_results.csv",
    index=False
)


print("\n==========================================")
print("CHART GENERATION COMPLETE")
print("==========================================")
print(f"Charts saved to: {OUTPUT_DIR}")
print("Results saved to: ../output/final_results.csv")