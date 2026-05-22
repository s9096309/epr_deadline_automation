# EPR Deadline Automation - Prototype

A lightweight Python prototype demonstrating an automated CRM cron job for tracking Extended Producer Responsibility (EPR) compliance deadlines. This project was developed as a proof-of-concept for the ecosistant technical assessment.

## 📌 Overview

This script simulates a daily automated process (designed to run via cron at 05:00 AM) that fetches customer compliance data and triggers necessary reminders. It uses an in-memory SQLite database to mock CRM data, ensuring the prototype is fully self-contained and requires zero setup or external dependencies.

## 🚀 Key Features

* **Zero-Setup Database:** Utilizes Python's native `sqlite3` in-memory database for immediate execution without local server configurations.
* **Smart Interval Matching:** Automatically calculates and targets precise compliance deadlines at 30-day, 14-day, and 3-day intervals.
* **Anti-Spam Protection (State Locking):** Implements a `last_notified_date` check to ensure customers are never spammed if the automation loop fails or restarts multiple times in a single day.
* **Multi-Channel Escalation:** Simulates standard email dispatches for early warnings and triggers high-priority Slack Webhook alerts for critical 3-day deadlines.

## 🛠️ Prerequisites

* Python 3.12 or higher
* No external libraries required (strictly uses the Python Standard Library: `sqlite3`, `datetime`).

## 💻 Usage

**1. Clone the Repository**

To get started, clone this repository to your local machine and navigate into the project directory:

```bash
git clone [https://github.com/s9096309/epr_deadline_automation.git](https://github.com/s9096309/epr_deadline_automation.git)
```
```bash
cd epr_deadline_automation
```
**2. Environment Setup**

This prototype relies strictly on Python's Standard Library (sqlite3, datetime), meaning there are no external dependencies to install.

However, if you prefer running it in an isolated environment, you can set up a virtual environment:

```Bash
# Create a virtual environment
python -m venv .venv
```
```bash
# Activate the virtual environment (Mac/Linux)
source .venv/bin/activate
```
```bash
# Activate the virtual environment (Windows)
.venv\Scripts\activate
```
**3. Run the Simulation**
Execute the main script from your terminal to trigger the daily cron job simulation:
```bash
python main.py
```

## 📈 Areas for Improvement & Future Scalability

While this prototype reliably handles the core logic, migrating this system to a production environment would require the following structural enhancements:

### 1. Data Fetching Optimization
* **Current State:** The script pulls all deadlines within a 31-day window into memory to evaluate them locally.
* **Production Fix:** As the database scales to tens of thousands of records, memory limits will be tested. The CRM API query should be refined to request *only* the exact target dates (e.g., `?deadline_in=30,14,3`) or utilize pagination logic to process records in controlled batches.

### 2. Granular State Locking
* **Current State:** The anti-spam lock prevents multiple executions on the same day (`last_notified_date == today`).
* **Production Fix:** A robust solution should track the specific milestone achieved (e.g., `notified_30_days = true`). This prevents bugs if a deadline is manually shifted in the CRM after an email has already been dispatched.

### 3. Workflow Trigger Validation
* **Current State:** Debugging assumes evaluating data inside the automation tool.
* **Production Fix:** Error analysis should incorporate "Step 0": Validating the time-based trigger itself (e.g., checking server cron logs) to ensure the platform isn't simply failing to initiate the sequence.

### 4. Tone & Notification Fatigue
* **Current State:** All email templates prioritize direct, urgent language. 
* **Production Fix:** Introduce an opt-out or frequency preference mechanism for users who suffer from notification fatigue. Additionally, soften the brand voice in the 30-day and 14-day emails, reserving the strict, urgent tone strictly for the critical 3-day escalation.