# Hotel CLV Prediction

A machine learning project for predicting **Customer Lifetime Value (CLV)** to support strategic revenue management in hotels.

The project uses **Random Forest and XGBoost regression models** to generate guest-level CLV predictions and provides a **Streamlit-based decision-support dashboard** for Revenue Managers and Marketing Teams.

## Project Objectives

The system is designed to:

- Analyse guest booking and behavioural characteristics related to CLV.
- Develop and compare Random Forest and XGBoost regression models.
- Generate guest-level CLV predictions.
- Categorise guests into High, Medium, and Low CLV tiers.
- Identify at-risk guests based on inactivity.
- Provide recommended actions to support customer retention and revenue management.
- Present predictions and guest insights through an interactive dashboard.
- Support action tracking by the Marketing Team.

## Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Machine Learning | Scikit-learn, XGBoost |
| Data Analysis | Pandas, NumPy |
| Dashboard | Streamlit |
| Database | Supabase PostgreSQL |
| Authentication | Supabase Auth |
| Model Storage | Supabase Storage |
| Development | Google Colab, VS Code |
| Version Control | Git and GitHub |

## Dashboard

Each user only sees the pages for their role.

### Revenue Manager

- Action Board, Guest Lookup and Segments
- At-Risk Guests, including changing the at-risk threshold and sending guests to Marketing as priority cases
- Predict a Booking, to get the predicted CLV of a new or returning booking
- Overriding a guest's recommended action, with a reason
- Exporting guest data as CSV

### Marketing Team

- Action Board, Guest Lookup and Segments
- Sending the recommended action to a guest by email or SMS
- Recording whether the guest came back

### System Administrator

- Inviting staff, changing roles and deactivating accounts
- Checking system health (the administrator cannot see guest data)

The dashboard is a **decision-support tool** for hotel staff, not a booking system.

## Machine Learning

The modelling stage uses two regression techniques:

- **Random Forest Regression**
- **XGBoost Regression**

Model performance is evaluated using:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R²

The models generate guest-level CLV predictions that are subsequently used by the dashboard.

Each record is one guest with a unique `guest_id`. The target is an **Estimated CLV** (historical booking value +
repeat-booking indicators), standardised to Kenyan Shillings. See [docs/data_pipeline.md](docs/data_pipeline.md)
for the notebook steps, category translations, Guest ID and CLV definition.

## How to Run

You will need Python 3.12 or newer, a free [Supabase](https://supabase.com) project, a Gmail account with an
app password (for emails) and an [Africa's Talking](https://africastalking.com) account (for SMS; the free
sandbox works for testing).

### 1. Build the model (optional)

The trained model and its predictions are already in `models/`, `results/` and `data/processed/`, so you can
skip this step. To rebuild them, open the notebooks in Google Colab and run them in order, from
`01_harmonize_dataset1.ipynb` to `08_evaluate_and_predict.ipynb`. Each notebook saves its output for the next one.

### 2. Set up the database

In your Supabase project, open the **SQL Editor** and run the files in `supabase/` in order, from `001_users.sql`
to `008_drop_marketing_consent.sql`. They create the tables and the access rules for each role.

### 3. Add your keys

Create a file called `.streamlit/secrets.toml` and fill in your own values below. This file is ignored by Git,
so your keys stay on your computer.

```toml
[supabase]
url = ""
publishable_key = ""
secret_key = ""

[app]
base_url = "http://localhost:8502"   # the dashboard's address, used in invitation emails

[messaging]
gmail_address = ""
gmail_app_password = ""              # a Gmail app password, not your normal password
sms_provider = "africastalking"
africastalking_username = "sandbox"
africastalking_api_key = ""
africastalking_sender_id = ""
daily_limit = 20                     # messages each staff member may send per day
```

### 4. Install and load the predictions

```bash
python -m venv frontend/.venv
frontend/.venv/Scripts/pip install -r frontend/requirements.txt
frontend/.venv/Scripts/python supabase/load_predictions.py
```

(On macOS or Linux, use `frontend/.venv/bin/` instead of `frontend/.venv/Scripts/`.)

### 5. Check that everything works

```bash
frontend/.venv/Scripts/python supabase/verify_setup.py
```

This tests the tables, the access rules and the loaded predictions, then removes its test data.
All checks should pass.

### 6. Create the first administrator and start the dashboard

```bash
frontend/.venv/Scripts/python supabase/create_admin_invite.py you@example.com
frontend/.venv/Scripts/streamlit run frontend/app.py
```

The first command emails an invite code. Open the dashboard, choose **Create an account**, and sign up with
that code. As the administrator you can then invite the Revenue Manager and the Marketing Team from the
**Administration** page.

## Project Structure

```text
hotel-clv-prediction/
│
├── notebooks/              # 01–08: data preparation, training and evaluation
├── data/                   # raw Kaggle datasets and processed outputs
├── models/                 # trained Random Forest and XGBoost models
├── results/                # metrics, test predictions and charts
├── docs/                   # data pipeline notes and design diagrams
│
├── supabase/
│   ├── 001_users.sql … 008_drop_marketing_consent.sql
│   ├── load_predictions.py     # loads predictions into the database
│   ├── verify_setup.py         # checks the setup and access rules
│   └── create_admin_invite.py  # invites the first administrator
│
├── frontend/
│   ├── app.py              # entry point and page routing
│   ├── auth.py             # sign-up, sign-in, invites and password reset
│   ├── predictor.py        # live CLV prediction for a booking
│   ├── messaging.py        # email and SMS
│   ├── data/repository.py  # reads and writes Supabase data
│   ├── views/              # one file per page
│   └── requirements.txt
│
├── .streamlit/
│   └── config.toml
│
└── README.md