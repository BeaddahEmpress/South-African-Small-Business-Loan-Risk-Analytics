Small Business Loan Risk Analysis

📌 Project Overview

Small businesses play an important role in economic growth, but lending to small businesses involves assessing the risk that borrowers may fail to repay their loans.

This project explores small business loan data to identify patterns associated with repayment outcomes and assess potential default risk. Using data analysis, SQL, Python, and interactive visualisation, the project aims to turn loan data into meaningful insights that can support more informed lending decisions.

🎯 Project Objectives

- Analyse small business loan and repayment data.
- Explore relationships between borrower characteristics, business information, income, and loan terms.
- Identify patterns associated with loan defaults.
- Assess how interest rates, monthly income, and years in business may relate to repayment outcomes.
- Present findings through clear visualisations and an interactive dashboard.

🛠️ Tools and Technologies

- Python — data processing and analysis
- Pandas — data manipulation and cleaning
- SQL / PostgreSQL — querying and analysing structured loan data
- Streamlit — interactive dashboard development
- Plotly — data visualisation
- CSV — dataset storage and input

📊 Dataset

The project uses "small_business_loans.csv", containing small business loan records for analytical purposes.

The dataset includes fields such as:

- "business_type" — business classification
- "years_in_business" — number of years the business has operated
- "monthly_income" — monthly business income
- "interest_rate" — interest rate associated with the loan
- "repayment_status" — loan repayment outcome
- "default_flag" — indicator used to analyse default risk

Note: Field descriptions and available columns should be confirmed against the actual dataset.

🔍 Analytical Approach

1. Data preparation: Load and inspect the dataset, check data types, and identify missing or inconsistent values.
2. Data analysis: Explore loan characteristics, business profiles, income, and repayment outcomes.
3. SQL analysis: Use queries to aggregate data, compare repayment patterns, and investigate default risk.
4. Visualisation: Present relevant trends and comparisons using charts.
5. Dashboard development: Use Streamlit to make the analysis accessible through an interactive interface.

💡 Business Value

The analysis can help demonstrate how data supports lending decisions by highlighting:

- Repayment patterns across business categories.
- Differences in repayment outcomes across business experience levels.
- Potential relationships between income, interest rates, and default outcomes.
- Areas where lenders may want to investigate risk more closely.

The analysis identifies patterns in the available data; it does not guarantee that a borrower will default or establish that a particular factor causes default.

🚀 Running the Project Locally

1. Clone the repository

git clone YOUR_GITHUB_REPOSITORY_URL
cd YOUR_REPOSITORY_FOLDER

Replace the placeholders with your actual repository URL and folder name.

2. Install the dependencies

pip install pandas streamlit plotly

Install any additional packages required by the application.

3. Run the dashboard

streamlit run app.py

The dashboard should open in your browser.

📁 Project Structure

Small-Business-Loan-Risk-Analysis/
├── app.py
├── small_business_loans.csv
├── your_analysis_notebook.ipynb
└── README.md

The notebook filename and any additional files should be updated to match the actual repository contents.

👩🏽‍💻 Author

Lerato Motloung

Aspiring Data Engineer interested in using SQL, Python, cloud technologies, and data visualisation to solve practical business problems.

This project forms part of my data portfolio, demonstrating practical experience in data analysis, database querying, and dashboard development.
