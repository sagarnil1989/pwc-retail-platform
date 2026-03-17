## 🧩 Implementation Details (Assignment Walkthrough)

### 🔹 Infrastructure Setup

For this assignment, I used **Terraform** to provision infrastructure in the Azure environment.

A **Service Principal** was created with **Owner-level access on the subscription**, which was used to deploy all required resources.

The core infrastructure components include:

- **Azure Databricks Workspace**
- **Azure Storage Account (Data Lake)**
- **Terraform Remote State (stored in the same storage account)**

---

### 🔹 Data Lake Design

The storage account acts as the **central data lake** for the platform.

It contains:

1. **Landing Container**
   - Used to receive raw input data from the **upstream system** (i.e., the source system providing input files).
   - Files are delivered in folders such as:
     ```
     day_1/
     day_2/
     ```

2. **Databricks Managed Storage**
   - Used internally by Databricks for:
     - Bronze, Silver, Gold data layers
     - Unity Catalog managed tables

---

### 🔹 Access Management

Access was configured as follows:

- Users were granted **Reader access at the Azure subscription level**
- Users were also given **read access to the Databricks workspace**

This ensures visibility into both infrastructure and data platform components without modification privileges.

---

### 🔹 Medallion Architecture (Core Data Model)

As part of the assignment, a **Medallion Architecture** was implemented:

- **Catalog Name:** `pwc_retail`
- **Schemas:**
  - `bronze`
  - `silver`
  - `gold`

Each layer serves a specific purpose:

| Layer | Description |
|------|-------------|
| Bronze | Raw ingestion from landing zone |
| Silver | Cleaned and transformed data with SCD2 |
| Gold | Business-ready aggregated tables |

---

### 🔹 Data Pipeline Design

A **Databricks Job Pipeline** named: Data Sync Pipeline Job TF 
was created (suffix `TF` indicates deployment via Terraform).

This pipeline orchestrates **three main tasks**:

---

#### 1. Landing → Bronze
- Implemented using a **Python notebook**
- Reads data from landing container
- Loads raw data into Bronze tables

---

#### 2. Bronze → Silver
- Implemented using **Lakeflow Declarative Pipeline**
- Required to support:
  - **Slowly Changing Dimension Type 2 (SCD2)**

👉 This is why a **pipeline (instead of notebook)** was used for the Silver layer.

---

#### 3. Silver → Gold
- Implemented using a **Python notebook**
- Creates aggregated, analytics-ready tables

---

### 🔹 Scheduling

The pipeline is configured to run:

- **Frequency:** Daily  
- **Days:** Monday to Friday  
- **Time:** 05:00 (configured in Databricks job schedule)

---

### 🔹 Data Loading Strategy

The system is designed to handle **incremental daily loads**.

Example workflow:

1. Upload data into: landing/day_1/
2. Run the pipeline → treated as **initial load**

3. Upload new data into: landing/day_2/

4. Run the pipeline again → treated as **incremental load**

---

### 🔹 Key Design Logic

- The pipeline determines whether data is new or already processed based on:
- **File path (e.g., day_1, day_2)**
- **Ingestion metadata**

👉 This allows multiple days of data to coexist in the landing zone.

👉 Only relevant data is processed in each run.

---

### 🔹 CI/CD Implementation

Two types of CI/CD were considered:

#### 1. Data Pipeline CI/CD
- Managed within **Databricks Jobs**
- Fully operational

#### 2. Infrastructure CI/CD
- Implemented using **GitHub Actions**
- Intended to automate:
- Terraform Plan
- Terraform Apply

⚠️ Note:
- Authentication via GitHub Actions (Service Principal) requires further setup
- Infrastructure deployment was executed successfully via **local execution (VS Code)**

---

### 🔹 Summary of Approach

- Terraform used for full infrastructure provisioning
- Azure Storage used as unified data lake
- Databricks used for compute and transformations
- Medallion architecture implemented using Unity Catalog
- SCD Type 2 implemented using Lakeflow pipelines
- Incremental processing based on file-based ingestion
- Pipeline orchestration via Databricks Jobs

---

## 🏁 Conclusion

This implementation demonstrates a **production-style data platform design**, combining:

- Infrastructure as Code
- Scalable data architecture
- Automated pipelines
- Governed data layers

It provides a strong foundation for **analytics, reporting, and future machine learning use cases**.