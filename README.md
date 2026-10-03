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

The dashboard provides role-specific views for two user groups.

### Revenue Manager

- Action Board
- Guest Lookup
- At-Risk Guests
- Guest Segments
- Predicted CLV information
- CLV tier information
- Guest data export
- At-risk threshold management

### Marketing Team

- Action Board
- Guest Lookup
- Guest Segments
- At-Risk Guests
- Recommended actions
- Action execution
- Action logging

The dashboard is designed as a **business analytics and decision-support interface**, rather than a hotel booking system.

## Machine Learning

The modelling stage uses two regression techniques:

- **Random Forest Regression**
- **XGBoost Regression**

Model performance is evaluated using:

- Mean Absolute Error (MAE)
- Root Mean Squared Error (RMSE)
- R²

The models generate guest-level CLV predictions that are subsequently used by the dashboard.

## Project Structure

```text
hotel-clv-prediction/
│
├── frontend/
│   ├── app.py
│   ├── auth.py
│   ├── style.py
│   ├── components.py
│   ├── charts.py
│   ├── utils.py
│   │
│   ├── data/
│   │   ├── mock_data.py
│   │   └── repository.py
│   │
│   └── views/
│       ├── home.py
│       ├── login.py
│       ├── signup.py
│       ├── action_board.py
│       ├── guest_lookup.py
│       ├── segments.py
│       └── at_risk_guests.py
│
├── supabase/
│   ├── 001_users.sql
│   ├── 002_app_tables.sql
│   ├── 003_outcomes_settings.sql
│   └── verify_setup.py
│
├── .streamlit/
│   └── config.toml
│
├── frontend/requirements.txt
├── pyrefly.toml
└── README.md