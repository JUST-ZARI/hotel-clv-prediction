# Data pipeline & CLV definition

Reference for the ML side of the Hotel CLV Decision Support System. Notebooks live in `notebooks/`, data in `data/`.

## Steps

| Step | Notebook | Output | What it does |
|---|---|---|---|
| 1 | `01_harmonize_dataset1.ipynb` | `data/processed/dataset1_harmonized.csv` | Renames Dataset 1 (`hotel_bookings.csv`, 119,390 bookings, 2015–2017) to the common schema; month names → numbers; fixes types. |
| 2 | `02_harmonize_dataset2.ipynb` | `data/processed/dataset2_harmonized.csv` | Renames Dataset 2 (`Hotel Reservations.csv`, 36,275 bookings, 2017–2018); `booking_status` → `is_canceled` (0/1); **translates category values into Dataset 1's wording** (below). |
| 3 | `03_merge_datasets.ipynb` | `data/processed/merged_dataset.csv` | Stacks both (155,665 rows, union of columns) and **creates `guest_id`**. |
| 4 | `04_eda_data_quality.ipynb` | — (inspection only) | Data quality and EDA, per source; lists what cleaning must handle. |
| 5 | *next* | — | Cleaning & preprocessing, Estimated CLV target, KSh conversion. |

Run in Colab (the first cell clones the `development` branch) or locally from the repository root.

## Category translation (Step 2)

| Column | Dataset 2 | → Dataset 1 |
|---|---|---|
| `meal_plan` | Meal Plan 1 / Meal Plan 2 / Meal Plan 3 / Not Selected | BB / HB / FB / SC |
| `market_segment` | Online / Offline | Online TA / Offline TA/TO |

`room_type_reserved` is **not** mapped: both sources use anonymised codes for different hotels (A–L vs `Room_Type 1–7`).

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

1. Duplicates — decide a policy for Dataset 1's 31,994 identical rows; **keep** Dataset 2's 10,275 same-detail rows
   (distinct booking IDs). Never de-duplicate while ignoring `booking_id`.
2. 37 invalid arrival dates (29 Feb 2018, Dataset 2).
3. Impossible/suspicious bookings: 793 with 0 nights, 180 with 0 guests, 1 negative ADR, 1 ADR of 5,400,
   2,504 with ADR = 0 (often complimentary).
4. Missing `country`, `agent_id`, `company_id` (Dataset 1); structural NaNs in source-only columns.
5. Post-outcome columns (`reservation_status`, `reservation_status_date`, `assigned_room_type`, `booking_changes`,
   `days_in_waiting_list`) — decide which may be model inputs.
6. Restore integer/date types after loading CSVs.
