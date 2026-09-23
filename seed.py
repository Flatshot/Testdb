"""Populate testdb with practice data for a district hospital.

Deterministic: the RNG is seeded and no wall-clock dates are used, so running
this twice produces byte-identical data. Safe to re-run -- it drops every table
first, so a schema change is picked up.

    python seed.py

The gaps below are deliberate. Questions about anti-joins, NULL handling,
open intervals and COUNT need something real to find:

  * patients who have never been admitted
  * admissions still open, so discharged_at is NULL -- and their current
    ward stay has no to_at, and their prescriptions may have no ended_on
  * observations with no temperature, procedures with no duration
  * patients whose blood group was never typed
  * staff with no ward (pharmacists, porters), and three who have never
    worked a shift
  * procedure types nobody has performed
  * a reporting FOREST: four division heads, and only they carry a division
"""

import random
from datetime import date, datetime, timedelta

import db

SEED = 731

# Admissions are spread across this window. observations is the big table --
# a reading every four to eight hours of every stay -- so it is where a
# fan-out or a runaway recursion is actually felt.
RANGE_START = datetime(2025, 1, 1, 0, 0)
RANGE_END = datetime(2026, 6, 30, 23, 59)
# The window closes with patients still in. Anything that would end after
# this instant is left open instead: a NULL discharge, a NULL stay end, a
# NULL prescription end.
SNAPSHOT = RANGE_END

TABLES = [
    "wards", "staff", "patients", "admissions", "ward_stays",
    "procedure_types", "procedures", "drugs", "prescriptions", "shifts",
    "observations",
]

WARDS = [("Nightingale", "cardiology", 24, 2), ("Seacole", "respiratory", 20, 2),
         ("Cavell", "orthopaedics", 28, 3), ("Barry", "general surgery", 30, 3),
         ("Fleming", "infectious diseases", 16, 4),
         ("Lister", "gastroenterology", 22, 1),
         ("Jenner", "paediatrics", 18, 1), ("Bevan", "geriatrics", 26, 4)]
PAEDIATRICS, GERIATRICS = 7, 8

FIRST = ["Aisha", "Bartholomew", "Cerys", "Dmitri", "Eleanor", "Farouk",
         "Grace", "Hamid", "Imogen", "Jonah", "Kwame", "Leila", "Marcus",
         "Nadia", "Oluwaseun", "Priya", "Quentin", "Rosa", "Samir", "Tamsin",
         "Umar", "Verity", "Wilfred", "Xiu", "Yusuf", "Zara"]
LAST = ["Achebe", "Baxter", "Chowdhury", "Dalgleish", "Ekwueme", "Fairweather",
        "Grzybowski", "Hollingsworth", "Iqbal", "Jankowski", "Khatri",
        "Lindqvist", "Mbeki", "Nakamura", "Okonjo", "Papadopoulos", "Quraishi",
        "Rasmussen", "Sowerby", "Tremblay", "Uddin", "Villanueva", "Whitcombe",
        "Yilmaz", "Zielinski"]

ROLES = ["consultant", "doctor", "nurse", "pharmacist", "porter"]
SALARY = {"consultant": (95_000, 140_000), "doctor": (42_000, 78_000),
          "nurse": (28_000, 46_000), "pharmacist": (38_000, 58_000),
          "porter": (22_000, 27_000)}
BLOOD = ["O+", "O+", "O+", "O-", "A+", "A+", "A-", "B+", "B-", "AB+", "AB-"]
POSTCODES = ["LS1", "LS2", "LS4", "LS6", "LS7", "LS8", "LS9", "LS11", "LS12",
             "LS13", "LS15", "LS16", "LS17", "BD3", "WF1"]
VIA = ["emergency"] * 55 + ["referral"] * 35 + ["transfer"] * 10
PRIORITY = ["immediate"] * 10 + ["urgent"] * 40 + ["routine"] * 50

PROCEDURE_TYPES = [
    ("SRG-01", "Appendicectomy", "surgical", 285_000),
    ("SRG-02", "Hip replacement", "surgical", 790_000),
    ("SRG-03", "Knee replacement", "surgical", 720_000),
    ("SRG-04", "Hernia repair", "surgical", 210_000),
    ("SRG-05", "Cholecystectomy", "surgical", 330_000),
    ("SRG-06", "Coronary bypass", "surgical", 1_450_000),
    ("SRG-07", "Pacemaker insertion", "surgical", 640_000),
    ("SRG-08", "Fracture fixation", "surgical", 410_000),
    ("SRG-09", "Tonsillectomy", "surgical", 150_000),
    ("SRG-10", "Skin graft", "surgical", 260_000),
    ("DIA-01", "CT scan", "diagnostic", 42_000),
    ("DIA-02", "MRI scan", "diagnostic", 68_000),
    ("DIA-03", "Ultrasound", "diagnostic", 18_000),
    ("DIA-04", "Endoscopy", "diagnostic", 55_000),
    ("DIA-05", "Colonoscopy", "diagnostic", 61_000),
    ("DIA-06", "Echocardiogram", "diagnostic", 36_000),
    ("DIA-07", "Angiogram", "diagnostic", 95_000),
    ("DIA-08", "Bronchoscopy", "diagnostic", 48_000),
    ("DIA-09", "Bone density scan", "diagnostic", 22_000),
    ("DIA-10", "Lumbar puncture", "diagnostic", 31_000),
    ("THR-01", "Blood transfusion", "therapeutic", 27_000),
    ("THR-02", "Dialysis session", "therapeutic", 38_000),
    ("THR-03", "Chemotherapy cycle", "therapeutic", 120_000),
    ("THR-04", "Physiotherapy course", "therapeutic", 15_000),
    ("THR-05", "Radiotherapy fraction", "therapeutic", 45_000),
    ("THR-06", "Joint injection", "therapeutic", 12_000),
    ("THR-07", "Nebuliser therapy", "therapeutic", 6_000),
    ("THR-08", "Wound debridement", "therapeutic", 19_000),
    ("THR-09", "Cardioversion", "therapeutic", 52_000),
    ("THR-10", "Plasma exchange", "therapeutic", 88_000),
]
# Three procedure types are never performed: the last of each category.
NEVER_PERFORMED = {"SRG-10", "DIA-10", "THR-10"}

DRUGS = [
    ("Amoxicillin", "tablet", 500, 12, 0), ("Paracetamol", "tablet", 500, 3, 0),
    ("Ibuprofen", "tablet", 400, 4, 0), ("Morphine", "injection", 10, 180, 1),
    ("Metformin", "tablet", 500, 6, 0), ("Atorvastatin", "tablet", 20, 9, 0),
    ("Ramipril", "tablet", 5, 7, 0), ("Salbutamol", "inhaler", 100, 250, 0),
    ("Insulin glargine", "injection", 100, 420, 0),
    ("Furosemide", "tablet", 40, 5, 0), ("Warfarin", "tablet", 3, 8, 0),
    ("Heparin", "injection", 5000, 210, 0), ("Omeprazole", "tablet", 20, 11, 0),
    ("Codeine", "tablet", 30, 15, 1), ("Diazepam", "tablet", 5, 9, 1),
    ("Gentamicin", "infusion", 80, 340, 0), ("Vancomycin", "infusion", 500, 610, 0),
    ("Ceftriaxone", "injection", 1000, 290, 0), ("Prednisolone", "tablet", 5, 6, 0),
    ("Amlodipine", "tablet", 5, 7, 0), ("Bisoprolol", "tablet", 5, 8, 0),
    ("Clopidogrel", "tablet", 75, 14, 0), ("Oxycodone", "tablet", 10, 95, 1),
    ("Fentanyl", "injection", 100, 260, 1), ("Ondansetron", "injection", 4, 120, 0),
    ("Dexamethasone", "injection", 4, 85, 0), ("Levothyroxine", "tablet", 50, 5, 0),
    ("Sertraline", "tablet", 50, 10, 0), ("Tramadol", "tablet", 50, 18, 1),
    ("Lorazepam", "injection", 2, 140, 1), ("Ipratropium", "inhaler", 20, 190, 0),
    ("Tiotropium", "inhaler", 18, 380, 0), ("Enoxaparin", "injection", 40, 330, 0),
    ("Apixaban", "tablet", 5, 32, 0), ("Digoxin", "tablet", 125, 9, 0),
    ("Doxycycline", "tablet", 100, 13, 0), ("Nitrofurantoin", "tablet", 50, 16, 0),
    ("Fluconazole", "tablet", 200, 24, 0), ("Piperacillin", "infusion", 4000, 720, 0),
    ("Propofol", "infusion", 200, 460, 0),
]


def _dt(d):
    return d.strftime("%Y-%m-%d %H:%M")


def _d(d):
    return d.strftime("%Y-%m-%d")


def seed():
    rng = random.Random(SEED)
    conn = db.connect()
    try:
        with conn:
            conn.execute("PRAGMA foreign_keys=OFF")
            for t in [r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                    " AND name NOT LIKE 'sqlite_%'")]:
                conn.execute(f'DROP TABLE IF EXISTS "{t}"')
        conn.executescript(db.SCHEMA_PATH.read_text(encoding="utf-8"))
        conn.execute("PRAGMA foreign_keys=ON")

        with conn:
            conn.executemany(
                "INSERT INTO wards (ward_id, name, specialty, beds, floor)"
                " VALUES (?, ?, ?, ?, ?)",
                [(i, *w) for i, w in enumerate(WARDS, 1)])

            # ---------------------------------------------------------- staff
            # A forest: four division heads report to nobody. Consultants
            # report to the head of Medicine or Surgery, doctors to a
            # consultant, senior nurses to the matron, nurses to a senior
            # nurse, pharmacists to the chief pharmacist, porters to the
            # matron. Three levels at the deepest.
            staff_rows = []
            heads = [(1, "consultant", "Medicine"), (2, "consultant", "Surgery"),
                     (3, "nurse", "Nursing"), (4, "pharmacist", "Pharmacy")]
            roles = (["consultant"] * 8 + ["doctor"] * 16 + ["nurse"] * 24
                     + ["pharmacist"] * 3 + ["porter"] * 5)
            consultants, senior_nurses = [], []
            for sid in range(1, 61):
                name = (FIRST[rng.randrange(len(FIRST))] + " "
                        + LAST[rng.randrange(len(LAST))])
                hired = date(2003, 1, 1) + timedelta(days=rng.randrange(8000))
                if sid <= 4:
                    _, role, division = heads[sid - 1]
                    boss = None
                else:
                    role, division = roles[sid - 5], None
                    if role == "consultant":
                        boss = rng.choice([1, 2])
                        consultants.append(sid)
                    elif role == "doctor":
                        boss = rng.choice(consultants)
                    elif role == "nurse":
                        if len(senior_nurses) < 6:
                            boss = 3
                            senior_nurses.append(sid)
                        else:
                            boss = rng.choice(senior_nurses)
                    elif role == "pharmacist":
                        boss = 4
                    else:
                        boss = 3
                ward = (None if role in ("pharmacist", "porter")
                        else rng.randrange(1, len(WARDS) + 1))
                lo, hi = SALARY[role]
                staff_rows.append((sid, name, role, ward, _d(hired), boss,
                                   division, rng.randrange(lo, hi)))
            # Shuffle the ids below the heads, so a manager's id is as often
            # above a report's as below it. Otherwise a one-level UPDATE
            # that reads its own earlier rows walks the whole tree by luck.
            perm = list(range(5, 61))
            random.Random(SEED + 1).shuffle(perm)
            remap = {i: (i if i <= 4 else perm[i - 5]) for i in range(1, 61)}
            staff_rows = sorted(
                (remap[s[0]], s[1], s[2], s[3], s[4],
                 None if s[5] is None else remap[s[5]], s[6], s[7])
                for s in staff_rows)
            consultants = [s[0] for s in staff_rows
                           if s[2] == "consultant" and s[0] > 4]
            # Two passes: a manager may now have a higher id than a report,
            # and foreign keys are checked as each statement ends.
            conn.executemany(
                "INSERT INTO staff (staff_id, name, role, ward_id, hired_on,"
                " reports_to, division, salary) VALUES (?, ?, ?, ?, ?, NULL, ?, ?)",
                [(s[0], s[1], s[2], s[3], s[4], s[6], s[7]) for s in staff_rows])
            conn.executemany(
                "UPDATE staff SET reports_to = ? WHERE staff_id = ?",
                [(s[5], s[0]) for s in staff_rows if s[5] is not None])
            all_consultants = [1, 2] + consultants
            doctors = [s[0] for s in staff_rows if s[2] == "doctor"]
            nurses_by_ward = {}
            for s in staff_rows:
                if s[2] == "nurse" and s[3]:
                    nurses_by_ward.setdefault(s[3], []).append(s[0])
            # Three people have never worked a shift.
            never_on_shift = {12, 27, 44}

            # ------------------------------------------------------- patients
            patients = []
            for pid in range(1, 2001):
                name = (FIRST[rng.randrange(len(FIRST))] + " "
                        + LAST[rng.randrange(len(LAST))])
                born = date(1930, 1, 1) + timedelta(days=rng.randrange(33_000))
                blood = None if rng.random() < 0.12 else rng.choice(BLOOD)
                patients.append((pid, name, _d(born), rng.choice("FM"), blood,
                                 rng.choice(POSTCODES)))
            conn.executemany(
                "INSERT INTO patients (patient_id, name, born_on, sex,"
                " blood_group, postcode_area) VALUES (?, ?, ?, ?, ?, ?)",
                patients)
            born_of = {p[0]: date.fromisoformat(p[2]) for p in patients}

            conn.executemany(
                "INSERT INTO procedure_types (code, name, category,"
                " tariff_pence) VALUES (?, ?, ?, ?)", PROCEDURE_TYPES)
            conn.executemany(
                "INSERT INTO drugs (drug_id, name, form, unit_mg, price_pence,"
                " controlled) VALUES (?, ?, ?, ?, ?, ?)",
                [(i, *d) for i, d in enumerate(DRUGS, 1)])

            # ----------------------------------------------------- admissions
            # 1,700 of the 2,000 patients are ever admitted; a third of
            # admissions go to someone already admitted before, so
            # readmissions are common enough to ask about.
            pool = rng.sample(range(1, 2001), k=1700)
            admitted_before = []
            adm_rows, stay_rows = [], []
            span_minutes = int((RANGE_END - RANGE_START).total_seconds() // 60)
            for aid in range(1, 6001):
                if admitted_before and rng.random() < 0.33:
                    pid = rng.choice(admitted_before)
                else:
                    pid = rng.choice(pool)
                admitted_before.append(pid)
                start = RANGE_START + timedelta(minutes=rng.randrange(span_minutes))
                # Length of stay: most short, a long tail up to a month.
                los_hours = min(rng.expovariate(1 / 72) + 4, 720)
                end = start + timedelta(hours=los_hours)
                age = (start.date() - born_of[pid]).days // 365
                if age < 16:
                    ward = PAEDIATRICS
                elif age >= 75 and rng.random() < 0.6:
                    ward = GERIATRICS
                else:
                    ward = rng.randrange(1, 7)
                discharged = None if end > SNAPSHOT else _dt(end)
                adm_rows.append((aid, pid, ward, rng.choice(all_consultants),
                                 _dt(start), discharged, rng.choice(VIA),
                                 rng.choice(PRIORITY)))
                # Ward stays: one for most, two or three for some. The first
                # is on the admitting ward; moves go to a different ward.
                n_stays = rng.choices([1, 2, 3], weights=[70, 25, 5])[0]
                cuts = sorted(rng.uniform(0.1, 0.9) for _ in range(n_stays - 1))
                bounds = [start] + [start + timedelta(hours=los_hours * c)
                                    for c in cuts] + [end]
                cur = ward
                for seq in range(1, n_stays + 1):
                    s_from, s_to = bounds[seq - 1], bounds[seq]
                    if seq > 1:
                        cur = rng.choice([w for w in range(1, 9) if w != cur])
                    to_at = None if s_to > SNAPSHOT else _dt(s_to)
                    stay_rows.append((aid, seq, cur, _dt(s_from), to_at))
                    if to_at is None:
                        break
            conn.executemany(
                "INSERT INTO admissions (admission_id, patient_id, ward_id,"
                " consultant_id, admitted_at, discharged_at, admitted_via,"
                " priority) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", adm_rows)
            conn.executemany(
                "INSERT INTO ward_stays (admission_id, stay_seq, ward_id,"
                " from_at, to_at) VALUES (?, ?, ?, ?, ?)", stay_rows)

            def stay_end(a):
                end = (datetime.strptime(a[5], "%Y-%m-%d %H:%M") if a[5]
                       else SNAPSHOT)
                return datetime.strptime(a[4], "%Y-%m-%d %H:%M"), end

            # ----------------------------------------------------- procedures
            codes = [p[0] for p in PROCEDURE_TYPES if p[0] not in NEVER_PERFORMED]
            proc, pid_ = [], 0
            for a in adm_rows:
                n = rng.choices([0, 1, 2], weights=[40, 45, 15])[0]
                start, end = stay_end(a)
                for _ in range(n):
                    pid_ += 1
                    at = start + timedelta(minutes=rng.randrange(
                        max(60, int((end - start).total_seconds() // 60))))
                    if at > SNAPSHOT:
                        at = start + timedelta(minutes=30)
                    dur = None if rng.random() < 0.10 else rng.randrange(15, 300)
                    proc.append((pid_, a[0], rng.choice(codes), _dt(at),
                                 rng.choice(all_consultants + doctors),
                                 rng.randrange(1, 7), dur))
            conn.executemany(
                "INSERT INTO procedures (procedure_id, admission_id, code,"
                " performed_at, surgeon_id, theatre, duration_minutes)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)", proc)

            # -------------------------------------------------- prescriptions
            rx, rid = [], 0
            prescribers = all_consultants + doctors
            for a in adm_rows:
                start, end = stay_end(a)
                for _ in range(rng.choices([0, 1, 2, 3, 4, 5],
                                           weights=[15, 25, 25, 18, 10, 7])[0]):
                    rid += 1
                    drug = rng.randrange(1, len(DRUGS) + 1)
                    began = start.date() + timedelta(days=rng.randrange(0, 2))
                    ends = began + timedelta(days=rng.randrange(1, 15))
                    ended = None if (a[5] is None and ends > SNAPSHOT.date()) \
                        else _d(min(ends, end.date()) if ends > end.date()
                                else ends)
                    unit = DRUGS[drug - 1][2]
                    rx.append((rid, a[0], drug, rng.choice(prescribers),
                               _d(began), ended, unit * rng.choice([1, 1, 2]),
                               rng.choice([1, 2, 2, 3, 4])))
            conn.executemany(
                "INSERT INTO prescriptions (prescription_id, admission_id,"
                " drug_id, prescribed_by, started_on, ended_on, dose_mg,"
                " times_per_day) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", rx)

            # --------------------------------------------------------- shifts
            shifts, shid = [], 0
            day = RANGE_START.date()
            while day <= RANGE_END.date():
                for s in staff_rows:
                    if s[0] in never_on_shift or rng.random() > 0.58:
                        continue
                    shid += 1
                    home = s[3] or rng.randrange(1, 9)
                    ward = home if rng.random() < 0.9 else rng.randrange(1, 9)
                    kind = "night" if rng.random() < 0.35 else "day"
                    hours = 12 if s[2] == "nurse" else 8
                    shifts.append((shid, s[0], ward, _d(day), kind, hours))
                day += timedelta(days=1)
            conn.executemany(
                "INSERT INTO shifts (shift_id, staff_id, ward_id, shift_date,"
                " kind, hours) VALUES (?, ?, ?, ?, ?, ?)", shifts)

            # --------------------------------------------------- observations
            # A reading every four to eight hours for the whole stay, capped.
            obs, oid = [], 0
            for a in adm_rows:
                start, end = stay_end(a)
                takers = nurses_by_ward.get(a[2]) or [3]
                t = start + timedelta(minutes=rng.randrange(10, 40))
                count = 0
                while t <= end and count < 60:
                    oid += 1
                    count += 1
                    temp = (None if rng.random() < 0.08
                            else round(rng.gauss(37.0, 0.6), 1))
                    obs.append((oid, a[0], _dt(t), rng.choice(takers),
                                rng.randrange(48, 125), rng.randrange(95, 175),
                                rng.randrange(55, 105), temp))
                    t += timedelta(minutes=rng.randrange(240, 480))
            conn.executemany(
                "INSERT INTO observations (obs_id, admission_id, taken_at,"
                " taken_by, heart_rate, systolic, diastolic, temp_c)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)", obs)
    finally:
        conn.close()
    return _counts()


def _counts():
    conn = db.connect()
    try:
        return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in TABLES}
    finally:
        conn.close()


if __name__ == "__main__":
    for table, n in seed().items():
        print(f"{table:>18}: {n:>7}")
    print(f"\nseeded {db.DB_PATH}")
