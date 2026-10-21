# Data pipeline & CLV definition

Reference for the ML side of the Hotel CLV Decision Support System. Notebooks live in `notebooks/`, data in `data/`.

## Steps

| Step | Notebook | Output | What it does |
|---|---|---|---|
| 1 | `01_harmonize_dataset1.ipynb` | `data/processed/dataset1_harmonized.csv` | Renames Dataset 1 (`hotel_bookings.csv`, 119,390 bookings, 2015–2017) to the common schema; month names → numbers; fixes types. |
| 2 | `02_harmonize_dataset2.ipynb` | `data/processed/dataset2_harmonized.csv` | Renames Dataset 2 (`Hotel Reservations.csv`, 36,275 bookings, 2017–2018); `booking_status` → `is_canceled` (0/1); **translates category values into Dataset 1's wording** (below). |
| 3 | `03_merge_datasets.ipynb` | `data/processed/merged_dataset.csv` | Stacks both (155,665 rows, union of columns) and **creates `guest_id`**. |
| 4 | `04_eda_data_quality.ipynb` | — (inspection only) | Data quality and EDA, per source; lists what cleaning must handle. |
| 5 | `05_preprocess.ipynb` | `data/processed/cleaned_dataset.csv`, `preprocessing_metadata.json` | Removes invalid records, caps outliers, fills gaps from the combined data, engineers features, converts to KSh, builds the Estimated CLV target, label-encodes categories. |

Run in Colab (the first cell clones the `development` branch) or locally from the repository root.

## Category translation (Step 2)

| Column | Dataset 2 | → Dataset 1 |
|---|---|---|
| `meal_plan` | Meal Plan 1 / Meal Plan 2 / Meal Plan 3 / Not Selected | BB / HB / FB / SC |
| `market_segment` | Online / Offline | Online TA / Offline TA/TO |
| `room_type_reserved` | Room_Type 1 … Room_Type 7 | A … G |

**Room-type rule:** the room number becomes the letter in the same position of the alphabet (1 → A … 7 → G). It
agrees with how common each type is: `Room_Type 1`/`A` are each source's most common room and `Room_Type 4`/`D`
the second most common (95% of the second source's bookings).

## One combined dataset

From Step 3 onwards the two sources are treated as **one dataset**: one vocabulary, one set of cleaning rules, and
gaps filled from the combined data rather than kept as a separate "Unknown" group. `source_dataset` is kept only as
a reference column and is **not** a model feature.

- **Categories only one source recorded** (`booking_channel`, `deposit_type`, `customer_type`, `hotel_type`, and the
  `has_agent` / `has_company` flags) → most common value among guests in the **same market segment**
  (e.g. 99% of *Online TA* guests book through TA/TO and have an agent).
- **Counts only one source recorded** (`booking_changes`, `num_babies`) → **median** of the combined data (0).
  The median is used rather than the mean because counts must be whole numbers.
- `country` → "Unknown" (not used by the model or dashboard; filling it would invent nationalities).

## Guest ID (Step 3)

Neither source identifies customers (Dataset 2's `booking_id` identifies a booking). Each record is therefore treated
as **one guest** and given a unique `guest_id` — `G-000001` … `G-155665`, Dataset 1 first, then Dataset 2. This is the
customer key used by the model, the Supabase `guests` table and the dashboard. IDs are assigned once, before
cleaning, so a guest keeps the same ID when other rows are removed.

## Estimated CLV (target, built in preprocessing)

> **Estimated CLV = historical booking value + repeat-booking indicators**

- **Booking value** = `adr × (stays_weekend_nights + stays_week_nights)` for bookings that were **not cancelled**
  (cancelled bookings contribute 0).
- **Repeat-booking indicators**: `is_repeated_guest`, `previous_bookings_not_canceled`, `previous_cancellations`.

Predictor variables considered: average daily rate, total nights, previous bookings not cancelled, previous
cancellations, is repeated guest, booking changes, market segment, booking channel (`distribution_channel`,
Dataset 1 only), lead time, number of adults / children, cancellation behaviour.

The exact weighting of the repeat-booking indicators, and which variables are inputs versus parts of the target,
is fixed in the preprocessing notebook so the model does not learn the target from its own ingredients.

## Currency

- Dataset 1 ADR is in **EUR** (Portuguese hotels).
- Dataset 2 does not state a currency; it is **assumed EUR** because its price level matches Dataset 1
  (median ADR 99.45 vs 94.58).
- All monetary values are converted to **Kenyan Shillings (KSh)** during preprocessing with **one** documented
  EUR→KSh rate (record the rate, its source and date in the preprocessing notebook).

## Carried into cleaning (from Step 4)

1. Duplicates — exact duplicates **without** a booking number are removed (31,832 in Step 5); rows with a
   booking number are kept even if their details match. Never de-duplicate while ignoring `booking_id`.
2. 37 invalid arrival dates (29 Feb 2018, Dataset 2).
3. Impossible/suspicious bookings: 793 with 0 nights, 180 with 0 guests, 1 negative ADR, 1 ADR of 5,400,
   2,504 with ADR = 0 (often complimentary).
4. Missing values — filled from the combined data (see *One combined dataset* above).
5. Post-outcome columns — `reservation_status`, `reservation_status_date`, `assigned_room_type` and
   `days_in_waiting_list` are dropped in Step 5; `booking_changes` (made before the stay) is kept as a feature.
6. Restore integer/date types after loading CSVs.
