# Data Import and Processing Script for Oracle Database

This project is a comprehensive Python-based application designed to process and import data from CSV and Excel files into an Oracle database. It supports advanced error handling, duplicate prevention, seamless integration with existing database schemas, and provides a modern graphical user interface (GUI) for data visualization and management.

## Features
- **Database Connectivity**:
  - Connects to an Oracle database using `oracledb`.
  - Supports multiple user roles with distinct privileges.
  
- **Data Import and Processing**:
  - Reads and processes data from two CSV files and one Excel file.
  - Handles duplicates and missing values in critical fields.
  - Supports `MERGE` operations for upserting data into key tables.
  - Implements compound triggers to prevent mutating table errors (e.g., ORA-04091).
  
- **Error Handling**:
  - Custom error handling for database constraints.
  - Logs invalid or skipped rows into a dedicated log file for review.
  
- **Graphical User Interface (GUI)**:
  - Modern PyQt5-based interface for interacting with the database.
  - Executes complex SQL queries involving joins, analytical functions, subqueries, and window functions.
  - Visualizes data through dynamic graphs using matplotlib.
  - Allows authorized users to query, modify, or delete data directly from the interface.
  
- **Automation and Optimization**:
  - Automates data loading and updates through Python scripts.
  - Optimizes database performance with indexing and query optimization techniques.
  
- **Logging and Reporting**:
  - Comprehensive logging of operations and errors.
  - Generates reports and visualizations for data analysis.

---

## Prerequisites
### Software Requirements
- **Python**: Version 3.8 or higher
- **Oracle Database**: Oracle 21c XE (Express Edition) or higher
- **Python Libraries**: Install using `pip install -r requirements.txt`
  - `oracledb`
  - `pandas`
  - `python-dotenv`
  - `PyQt5`
  - `matplotlib`

### Environment Variables
Create a `.env` file in the project directory with the following variables:

```dotenv
# Database Connection Details
ORA_HOST=your_oracle_host
ORA_PORT=your_oracle_port
ORA_SERVICE=your_oracle_service
ADMIN_USER_PASS=your_admin_user_password

# File Paths
CSV1=data/2024_LoL_esports_match_data_from_OraclesElixir1.csv
CSV2=data/2024_LoL_esports_match_data_from_OraclesElixir_gamedata.csv
XLS1=data/2024_LoL_esports_match_data_from_OraclesElixir.xlsx
```

> **Note**: Ensure that the `.env` file is **not** committed to version control to protect sensitive credentials.

---

## Installation
1. **Clone the Repository**:
   ```bash
   git clone https://github.com/SolaDevSolide/ADBMProject.git
   cd ADBMProject
   ```

2. **Install Required Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   - Create a `.env` file as described in the **Prerequisites** section.
   - Place your CSV and Excel files in the `data/` directory as per the `.env` file.

4. **Deploy the Database Schema**:
   - **For Windows**:
      - Open PowerShell.
      - Navigate to the `scripts/` directory.
      - Run the PowerShell deployment script:
        ```powershell
        ./deploy.ps1
        ```
   - **For Unix/Linux**:
      - Open Terminal.
      - Navigate to the `scripts/` directory.
      - Run the shell deployment script:
        ```bash
        ./deploy.sh
        ```

5. **Run the Data Import Script**:
   ```bash
   python scripts/populate_lol_data.py
   ```

6. **Launch the Graphical Interface**:
   ```bash
   python interface.py
   ```

---

## Logging
- **Invalid Rows**: The script logs invalid or skipped rows into `scripts/invalid_rows.log`. Ensure this file is in the `scripts/` directory for proper logging.
- **General Logs**: Operational logs are maintained in `scripts/app.log` for detailed review and debugging.

---

## Error Handling
### Common Errors
1. **ORA-04091: Table is Mutating**
   - **Cause**: Attempting to query or modify the same table within a row-level trigger.
   - **Solution**: Implemented a **compound trigger** to handle such scenarios without causing mutating table errors.

2. **ORA-01400: Cannot Insert NULL**
   - **Cause**: Missing critical values in required fields.
   - **Solution**: Ensured the script cleans and validates CSV/Excel data before import.

3. **ORA-00001: Unique Constraint Violation**
   - **Cause**: Attempting to insert duplicate records that violate unique constraints.
   - **Solution**: Utilized `MERGE` operations to upsert data, preventing duplicates.

4. **ORA-02291: Integrity Constraint Violation**
   - **Cause**: Foreign key constraints are violated due to missing referenced records.
   - **Solution**: Ensured all referenced records (e.g., players, teams, champions) exist before importing related data.

### Logs and Debugging
- Errors are printed in the console and logged in `scripts/app.log` for comprehensive debugging.
- Review `scripts/invalid_rows.log` to identify and rectify data issues.

---

## Project Structure
```
ADBMProject/
├── data/
│   ├── 2024_LoL_esports_match_data_from_OraclesElixir.xlsx
│   ├── 2024_LoL_esports_match_data_from_OraclesElixir1.csv
│   └── 2024_LoL_esports_match_data_from_OraclesElixir_gamedata.csv
├── research/
│   ├── CoreEntitiesDiagram.puml
│   ├── Data Analysis.ipynb
│   ├── StatsandPicksBansDiagram.puml
│   └── tables.puml
├── scripts/
│   ├── deploy.ps1
│   ├── deploy.sh
│   ├── invalid_rows.log
│   ├── lol_schema_setup.sql
│   ├── lol_schema_setup_template.sql
│   └── populate_lol_data.py
├── .env
├── .gitignore
├── interface.py
├── interface.spec
├── project-structure.txt
├── README.md
└── requirements.txt
```

---

## How to Contribute
1. **Fork the Repository**.
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Commit Your Changes**:
   ```bash
   git commit -m "Add your feature description"
   ```
4. **Push to the Branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
5. **Open a Pull Request**.

---

## Acknowledgements
- **Python Libraries**: `oracledb`, `pandas`, `python-dotenv`, `PyQt5`, `matplotlib`
- **Database**: Oracle 21c XE
- **GUI Framework**: PyQt5
- **Package Builder**: PyInstaller

---

## References
- **Oracle Error Documentation**: [ORA-04091](https://docs.oracle.com/en/database/oracle/oracle-database/21/server/ORACLE-ERR-04091.html)
- **PyQt5 Documentation**: [https://doc.qt.io/qtforpython](https://doc.qt.io/qtforpython)
- **Python Libraries**:
   - [oracledb](https://pypi.org/project/oracledb/)
   - [pandas](https://pandas.pydata.org/)
   - [python-dotenv](https://pypi.org/project/python-dotenv/)
   - [matplotlib](https://matplotlib.org/)
- **Project Report**: Refer to the LaTeX report for detailed project documentation.

---