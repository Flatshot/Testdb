-- Schema for testdb: a district hospital.
-- Applied by db.init_db(); every statement is safe to re-run.
--
-- The fourth schema in this repo, after a college, a field-service workshop
-- and a railway. Chosen for a shape none of those had: INTERVALS. Almost every
-- fact here has a start and an end --
--
--   admissions            admitted_at .. discharged_at, a datetime pair; NULL
--                         discharged_at means the patient is still in. Two
--                         admissions OVERLAP, a ward has an OCCUPANCY at any
--                         instant, a patient can be READMITTED within 30 days
--                         -- none of which a railway timetable could ask.
--   ward_stays            the ordered sequence inside an admission (stay_seq),
--                         each stay its own interval on one ward
--   prescriptions         started_on .. ended_on, dates, NULL while ongoing
--   observations          a time series, four to six readings a day, and by
--                         far the biggest table -- the one a fan-out is felt on
--
-- Other shapes carried over on purpose, so familiar questions have a home:
--
--   staff.reports_to      a hierarchy, this time a FOREST: four division heads
--                         report to nobody, and only they carry a division
--   procedure_types.tariff_pence, drugs.price_pence
--                         money as INTEGER, so shares hit integer division
--   admissions.priority   a category whose natural order is not alphabetical
--                         ('immediate' < 'urgent' < 'routine')
--   shifts                a rota: one row per person per day, day or night
--   datetimes are 'YYYY-MM-DD HH:MM' text; dates are 'YYYY-MM-DD'. julianday()
--                         turns either into a number you can subtract.
--
-- Deliberate gaps: patients never admitted, admissions not yet discharged,
-- ward stays with no end, prescriptions still running, observations with no
-- temperature, procedures with no recorded duration, patients with no known
-- blood group, staff with no ward, staff who have never worked a shift, and
-- procedure types nobody has performed.

CREATE TABLE IF NOT EXISTS wards (
    ward_id   INTEGER PRIMARY KEY,
    name      TEXT    NOT NULL UNIQUE,
    specialty TEXT    NOT NULL,
    beds      INTEGER NOT NULL CHECK (beds > 0),
    floor     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS staff (
    staff_id   INTEGER PRIMARY KEY,
    name       TEXT    NOT NULL,
    role       TEXT    NOT NULL CHECK (role IN ('consultant', 'doctor', 'nurse',
                                                'pharmacist', 'porter')),
    -- NULL for pharmacists and porters, who belong to no ward
    ward_id    INTEGER REFERENCES wards(ward_id),
    hired_on   TEXT    NOT NULL,
    -- NULL for the four division heads
    reports_to INTEGER REFERENCES staff(staff_id),
    -- set only on the division heads; everyone else inherits it via the tree
    division   TEXT,
    -- annual salary in whole pounds
    salary     INTEGER NOT NULL CHECK (salary > 0)
);

CREATE TABLE IF NOT EXISTS patients (
    patient_id    INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    born_on       TEXT NOT NULL,
    sex           TEXT NOT NULL CHECK (sex IN ('F', 'M')),
    -- NULL where never typed
    blood_group   TEXT CHECK (blood_group IS NULL OR blood_group IN
                             ('O+', 'O-', 'A+', 'A-', 'B+', 'B-', 'AB+', 'AB-')),
    postcode_area TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS admissions (
    admission_id  INTEGER PRIMARY KEY,
    patient_id    INTEGER NOT NULL REFERENCES patients(patient_id),
    -- the ward admitted TO; later moves are in ward_stays
    ward_id       INTEGER NOT NULL REFERENCES wards(ward_id),
    consultant_id INTEGER NOT NULL REFERENCES staff(staff_id),
    admitted_at   TEXT    NOT NULL,
    -- NULL while the patient is still in
    discharged_at TEXT,
    admitted_via  TEXT    NOT NULL CHECK (admitted_via IN ('emergency', 'referral',
                                                            'transfer')),
    priority      TEXT    NOT NULL CHECK (priority IN ('immediate', 'urgent',
                                                        'routine'))
);

-- The ordered sequence: where the patient was, in order. stay_seq counts
-- from 1 within each admission; the first stay's ward is admissions.ward_id.
CREATE TABLE IF NOT EXISTS ward_stays (
    admission_id INTEGER NOT NULL REFERENCES admissions(admission_id),
    stay_seq     INTEGER NOT NULL CHECK (stay_seq > 0),
    ward_id      INTEGER NOT NULL REFERENCES wards(ward_id),
    from_at      TEXT    NOT NULL,
    -- NULL for the current stay of an admission still open
    to_at        TEXT,
    PRIMARY KEY (admission_id, stay_seq)
);

CREATE TABLE IF NOT EXISTS procedure_types (
    code         TEXT    PRIMARY KEY,
    name         TEXT    NOT NULL UNIQUE,
    category     TEXT    NOT NULL CHECK (category IN ('surgical', 'diagnostic',
                                                       'therapeutic')),
    -- what the hospital is paid for one, in whole pence
    tariff_pence INTEGER NOT NULL CHECK (tariff_pence >= 0)
);

CREATE TABLE IF NOT EXISTS procedures (
    procedure_id     INTEGER PRIMARY KEY,
    admission_id     INTEGER NOT NULL REFERENCES admissions(admission_id),
    code             TEXT    NOT NULL REFERENCES procedure_types(code),
    performed_at     TEXT    NOT NULL,
    surgeon_id       INTEGER NOT NULL REFERENCES staff(staff_id),
    theatre          INTEGER NOT NULL CHECK (theatre BETWEEN 1 AND 6),
    -- NULL where nobody recorded it
    duration_minutes INTEGER CHECK (duration_minutes IS NULL OR duration_minutes > 0)
);

CREATE TABLE IF NOT EXISTS drugs (
    drug_id     INTEGER PRIMARY KEY,
    name        TEXT    NOT NULL UNIQUE,
    form        TEXT    NOT NULL CHECK (form IN ('tablet', 'injection', 'infusion',
                                                 'inhaler')),
    unit_mg     INTEGER NOT NULL CHECK (unit_mg > 0),
    -- per unit, whole pence
    price_pence INTEGER NOT NULL CHECK (price_pence >= 0),
    controlled  INTEGER NOT NULL CHECK (controlled IN (0, 1))
);

CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id INTEGER PRIMARY KEY,
    admission_id    INTEGER NOT NULL REFERENCES admissions(admission_id),
    drug_id         INTEGER NOT NULL REFERENCES drugs(drug_id),
    prescribed_by   INTEGER NOT NULL REFERENCES staff(staff_id),
    started_on      TEXT    NOT NULL,
    -- NULL while the course is still running
    ended_on        TEXT,
    dose_mg         INTEGER NOT NULL CHECK (dose_mg > 0),
    times_per_day   INTEGER NOT NULL CHECK (times_per_day BETWEEN 1 AND 6)
);

CREATE TABLE IF NOT EXISTS shifts (
    shift_id   INTEGER PRIMARY KEY,
    staff_id   INTEGER NOT NULL REFERENCES staff(staff_id),
    ward_id    INTEGER NOT NULL REFERENCES wards(ward_id),
    shift_date TEXT    NOT NULL,
    kind       TEXT    NOT NULL CHECK (kind IN ('day', 'night')),
    hours      INTEGER NOT NULL CHECK (hours IN (8, 12)),
    UNIQUE (staff_id, shift_date)
);

CREATE TABLE IF NOT EXISTS observations (
    obs_id       INTEGER PRIMARY KEY,
    admission_id INTEGER NOT NULL REFERENCES admissions(admission_id),
    taken_at     TEXT    NOT NULL,
    taken_by     INTEGER NOT NULL REFERENCES staff(staff_id),
    heart_rate   INTEGER NOT NULL CHECK (heart_rate BETWEEN 20 AND 250),
    systolic     INTEGER NOT NULL CHECK (systolic BETWEEN 50 AND 260),
    diastolic    INTEGER NOT NULL CHECK (diastolic BETWEEN 30 AND 160),
    -- NULL where the temperature was not taken
    temp_c       REAL    CHECK (temp_c IS NULL OR temp_c BETWEEN 30 AND 43)
);

CREATE INDEX IF NOT EXISTS idx_staff_reports     ON staff(reports_to);
CREATE INDEX IF NOT EXISTS idx_patients_name     ON patients(name COLLATE NOCASE);
CREATE INDEX IF NOT EXISTS idx_adm_patient       ON admissions(patient_id);
CREATE INDEX IF NOT EXISTS idx_adm_ward_time     ON admissions(ward_id, admitted_at);
CREATE INDEX IF NOT EXISTS idx_adm_admitted      ON admissions(admitted_at);
CREATE INDEX IF NOT EXISTS idx_stays_ward        ON ward_stays(ward_id);
CREATE INDEX IF NOT EXISTS idx_proc_admission    ON procedures(admission_id);
CREATE INDEX IF NOT EXISTS idx_proc_surgeon      ON procedures(surgeon_id);
CREATE INDEX IF NOT EXISTS idx_rx_admission      ON prescriptions(admission_id);
CREATE INDEX IF NOT EXISTS idx_rx_drug           ON prescriptions(drug_id);
CREATE INDEX IF NOT EXISTS idx_shifts_ward_date  ON shifts(ward_id, shift_date);
CREATE INDEX IF NOT EXISTS idx_shifts_staff      ON shifts(staff_id);
CREATE INDEX IF NOT EXISTS idx_obs_admission     ON observations(admission_id, taken_at);
CREATE INDEX IF NOT EXISTS idx_obs_taken         ON observations(taken_at);
