import os
import psycopg2
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ============================================================
# SMART RF SPECTRUM MONITORING
# SIMULATION ENGINE
# ============================================================

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT")),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Reproducible simulation
random.seed(42)

NUM_TIME_SLOTS = 100
SCANS_PER_STRATEGY = 500

# Each time slot represents 1 second
SLOT_DURATION_SECONDS = 1

# Scanner dwell time
DWELL_TIME_MS = 200

STRATEGIES = [
    "Sequential",
    "Random",
    "Adaptive"
]

START_TIME = datetime(2026, 1, 1, 10, 0, 0)


# ============================================================
# DATABASE CONNECTION
# ============================================================

connection = psycopg2.connect(**DB_CONFIG)
cursor = connection.cursor()

print("Connected to PostgreSQL.")


# ============================================================
# LOAD BANDS
# ============================================================

cursor.execute("""
    SELECT
        band_id,
        priority
    FROM frequency_bands
    ORDER BY band_id;
""")

bands = cursor.fetchall()

print(f"Loaded {len(bands)} frequency bands.")


# ============================================================
# LOAD EMITTERS
# ============================================================

cursor.execute("""
    SELECT
        emitter_id,
        priority
    FROM emitters
    ORDER BY emitter_id;
""")

emitters = cursor.fetchall()

print(f"Loaded {len(emitters)} emitters.")


# ============================================================
# CLEAR PREVIOUS SIMULATION
# ============================================================

print("Clearing previous simulation data...")

cursor.execute("DELETE FROM intercepts;")
cursor.execute("DELETE FROM observations;")
cursor.execute("DELETE FROM scans;")
cursor.execute("DELETE FROM transmissions;")

connection.commit()


# ============================================================
# GENERATE GROUND-TRUTH TRANSMISSIONS
# ============================================================

print("Generating simulated transmissions...")

transmissions = []

transmission_id = 1


# Give some bands higher signal activity.
# This creates meaningful patterns for the adaptive scheduler.

signal_band_weights = {
    1: 1,
    2: 1,
    3: 4,
    4: 1,
    5: 1,
    6: 3,
    7: 1,
    8: 5,
    9: 1,
    10: 2
}

weighted_band_list = []

for band_id, weight in signal_band_weights.items():
    weighted_band_list.extend([band_id] * weight)


for slot in range(NUM_TIME_SLOTS):

    slot_start = START_TIME + timedelta(
        seconds=slot
    )

    # 1-3 transmissions per slot
    number_of_transmissions = random.randint(1, 3)

    for _ in range(number_of_transmissions):

        emitter_id, _ = random.choice(emitters)

        band_id = random.choice(
            weighted_band_list
        )

        # Transmission begins at a random point
        # within the time slot.
        start_offset = random.uniform(
            0.0,
            0.5
        )

        transmission_start = (
            slot_start
            + timedelta(seconds=start_offset)
        )

        # Longer duration makes scanner timing meaningful.
        duration = random.uniform(
            0.5,
            1.5
        )

        transmission_end = (
            transmission_start
            + timedelta(seconds=duration)
        )

        signal_strength = round(
            random.uniform(-75, -35),
            2
        )

        cursor.execute("""
            INSERT INTO transmissions (
                transmission_id,
                emitter_id,
                band_id,
                start_time,
                end_time,
                signal_strength_dbm
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            transmission_id,
            emitter_id,
            band_id,
            transmission_start,
            transmission_end,
            signal_strength
        ))

        transmissions.append({
            "transmission_id": transmission_id,
            "emitter_id": emitter_id,
            "band_id": band_id,
            "start_time": transmission_start,
            "end_time": transmission_end,
            "signal_strength": signal_strength
        })

        transmission_id += 1


print(
    f"Generated {len(transmissions)} transmissions."
)


# ============================================================
# SCANNING
# ============================================================

scan_id = 1
observation_id = 1
intercept_id = 1


# Adaptive memory
recent_hits = {
    band_id: 0
    for band_id, _ in bands
}

recent_misses = {
    band_id: 0
    for band_id, _ in bands
}


# Last time a signal was detected in each band
last_detection = {
    band_id: None
    for band_id, _ in bands
}


# ============================================================
# HELPER FUNCTION
# ============================================================

def find_active_transmission(
    band_id,
    scan_time
):
    """
    Find a transmission that is active in the
    selected band at the scan time.
    """

    active = []

    for transmission in transmissions:

        if transmission["band_id"] != band_id:
            continue

        if (
            transmission["start_time"]
            <= scan_time
            <= transmission["end_time"]
        ):
            active.append(transmission)

    if not active:
        return None

    # If multiple transmissions overlap,
    # use the strongest one.
    return max(
        active,
        key=lambda x: x["signal_strength"]
    )


# ============================================================
# RUN EACH STRATEGY
# ============================================================

for strategy in STRATEGIES:

    print(
        f"Running {strategy} strategy..."
    )

    sequential_index = 0

    for scan_number in range(
        SCANS_PER_STRATEGY
    ):

        # Each strategy gets its own timeline.
        #
        # 500 scans × 200 ms = 100 seconds.

        scan_time = (
            START_TIME
            + timedelta(
                milliseconds=
                scan_number * DWELL_TIME_MS
            )
        )


        # ====================================================
        # SELECT BAND
        # ====================================================

        if strategy == "Sequential":

            band_id = bands[
                sequential_index
                % len(bands)
            ][0]

            sequential_index += 1


        elif strategy == "Random":

            band_id = random.choice(
                bands
            )[0]


        else:

            # =================================================
            # ADAPTIVE SCORING
            # =================================================

            scored_bands = []

            for band_id_candidate, original_priority in bands:

                score = (
                    original_priority
                    + (3.0 * recent_hits[band_id_candidate])
                    - (0.5 * recent_misses[band_id_candidate])
                )

                # Give a bonus to bands where a detection
                # happened recently.
                if last_detection[
                    band_id_candidate
                ] is not None:

                    elapsed = (
                        scan_time
                        - last_detection[
                            band_id_candidate
                        ]
                    ).total_seconds()

                    if elapsed < 5:
                        score += 5

                    elif elapsed < 10:
                        score += 2

                scored_bands.append(
                    (
                        band_id_candidate,
                        score
                    )
                )


            scored_bands.sort(
                key=lambda x: x[1],
                reverse=True
            )


            # 80% exploitation
            # 20% exploration

            if random.random() < 0.80:

                band_id = scored_bands[0][0]

            else:

                band_id = random.choice(
                    bands
                )[0]


        # ====================================================
        # RECORD SCAN
        # ====================================================

        cursor.execute("""
            INSERT INTO scans (
                scan_id,
                band_id,
                strategy,
                scan_time,
                dwell_time_ms
            )
            VALUES (%s, %s, %s, %s, %s);
        """, (
            scan_id,
            band_id,
            strategy,
            scan_time,
            DWELL_TIME_MS
        ))


        # ====================================================
        # GROUND TRUTH
        # ====================================================

        active_transmission = (
            find_active_transmission(
                band_id,
                scan_time
            )
        )

        actual_signal = (
            active_transmission is not None
        )


        # ====================================================
        # RECEIVER MODEL
        # ====================================================

        if actual_signal:

            detection_probability = {
                "Sequential": 0.72,
                "Random": 0.60,
                "Adaptive": 0.88
            }[strategy]

            received_signal = (
                random.random()
                < detection_probability
            )

            snr_db = round(
                random.uniform(5, 25),
                2
            )

        else:

            false_alarm_probability = {
                "Sequential": 0.08,
                "Random": 0.10,
                "Adaptive": 0.05
            }[strategy]

            received_signal = (
                random.random()
                < false_alarm_probability
            )

            snr_db = round(
                random.uniform(-10, 5),
                2
            )


        # ====================================================
        # RECORD OBSERVATION
        # ====================================================

        cursor.execute("""
            INSERT INTO observations (
                observation_id,
                scan_id,
                band_id,
                received_signal,
                actual_signal,
                snr_db
            )
            VALUES (%s, %s, %s, %s, %s, %s);
        """, (
            observation_id,
            scan_id,
            band_id,
            received_signal,
            actual_signal,
            snr_db
        ))


        # ====================================================
        # UPDATE ADAPTIVE MEMORY
        # ====================================================

        if strategy == "Adaptive":

            if actual_signal and received_signal:

                recent_hits[band_id] += 1

                last_detection[
                    band_id
                ] = scan_time

            elif actual_signal:

                recent_misses[
                    band_id
                ] += 1


        # ====================================================
        # SUCCESSFUL INTERCEPTION
        # ====================================================

        if (
            actual_signal
            and received_signal
            and active_transmission
            is not None
        ):

            # Small receiver processing delay
            processing_delay = random.uniform(
                0.02,
                0.08
            )

            intercept_time = (
                scan_time
                + timedelta(
                    seconds=processing_delay
                )
            )

            # The important metric:
            #
            # time from transmission beginning
            # until successful interception.

            time_error_ms = (
                intercept_time
                - active_transmission[
                    "start_time"
                ]
            ).total_seconds() * 1000


            cursor.execute("""
                INSERT INTO intercepts (
                    intercept_id,
                    observation_id,
                    emitter_id,
                    intercept_time,
                    time_error_ms
                )
                VALUES (%s, %s, %s, %s, %s);
            """, (
                intercept_id,
                observation_id,
                active_transmission[
                    "emitter_id"
                ],
                intercept_time,
                round(
                    time_error_ms,
                    2
                )
            ))

            intercept_id += 1


        scan_id += 1
        observation_id += 1


# ============================================================
# SAVE EVERYTHING
# ============================================================

connection.commit()


# ============================================================
# SUMMARY
# ============================================================

print()
print("============================================")
print("SIMULATION COMPLETE")
print("============================================")
print(
    f"Transmissions : {len(transmissions)}"
)
print(
    f"Scans         : {scan_id - 1}"
)
print(
    f"Observations  : {observation_id - 1}"
)
print(
    f"Intercepts    : {intercept_id - 1}"
)
print("============================================")


cursor.close()
connection.close()

print("Database connection closed.")