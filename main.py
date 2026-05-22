import sqlite3
import datetime


# ==========================================
# 1. DATABASE SETUP & MOCK DATA
# ==========================================
def setup_database():
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''
        CREATE TABLE customers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE epr_tasks (
            id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            country TEXT,
            waste_stream TEXT,
            next_epr_deadline DATE,
            last_notified_date DATE,
            FOREIGN KEY(customer_id) REFERENCES customers(id)
        )
    ''')

    # Calculate dynamic dates for testing
    today = datetime.date.today()
    date_30 = today + datetime.timedelta(days=30)
    date_14 = today + datetime.timedelta(days=14)
    date_3 = today + datetime.timedelta(days=3)
    date_ignore = today + datetime.timedelta(days=10)  # No notification needed

    # Insert Mock Customers
    customers = [
        (1, 'TechStore GmbH', 'contact@techstore.de'),
        (2, 'EcoPackaging Ltd', 'info@ecopack.co.uk'),
        (3, 'Global Goods', 'hello@globalgoods.com'),
        (4, 'Silent Partner Inc', 'quiet@partner.com'),
        (5, 'Spam Check Co', 'spam@check.com')
    ]
    cursor.executemany('INSERT INTO customers VALUES (?, ?, ?)', customers)

    # Insert Mock Tasks (convert to strings to prevent DeprecationWarning)
    tasks = [
        (101, 1, 'DE', 'Packaging', str(date_30), None),
        (102, 2, 'FR', 'WEEE', str(date_14), None),
        (103, 3, 'ES', 'Batteries', str(date_3), None),
        (104, 4, 'IT', 'Packaging', str(date_ignore), None),
        (105, 5, 'AT', 'WEEE', str(date_30), str(today))
    ]
    cursor.executemany('INSERT INTO epr_tasks VALUES (?, ?, ?, ?, ?, ?)', tasks)
    conn.commit()
    return conn


# ==========================================
# 2. SIMULATED ACTIONS (MOCKS)
# ==========================================
def send_email(template, customer_name, waste_stream, country, deadline):
    print("-" * 60)
    print(f"📧 [OUTGOING EMAIL] To: {customer_name}")
    print("-" * 60)

    if template == "30_days":
        print(f"Betreff: ⏳ 30 Tage verbleibend: Deine EPR-Meldefrist für {country} ({waste_stream})\n")
        print(f"Hallo {customer_name},\n")
        print(
            f"dies ist eine frühzeitige Erinnerung: Die gesetzliche Recycling-Meldefrist für {waste_stream} in {country} endet am {deadline}.")
        print("Bitte bereite deine Verkaufsdaten rechtzeitig vor, um Strafgebühren zu vermeiden.\n")
        print("🔗 [Jetzt Daten im Portal einreichen]")

    elif template == "14_days":
        print(f"Betreff: ⚠️ Wichtig: Nur noch 14 Tage für deine EPR-Meldung in {country}\n")
        print(f"Hallo {customer_name},\n")
        print(
            f"die Frist für deine EPR-Compliance bezüglich {waste_stream} in {country} rückt näher: Stichtag ist der {deadline}.")
        print("Vermeide unnötigen Stress und reiche deine Mengenmeldungen jetzt ein.\n")
        print("🔗 [Direkt zur Meldung]")

    elif template == "3_days":
        print(f"Betreff: 🚨 Letzte Warnung: EPR-Frist für {country} läuft in 3 Tagen ab!\n")
        print(f"Hallo {customer_name},\n")
        print(
            f"Achtung: Es verbleiben nur noch 3 Tage. Für {waste_stream} in {country} endet die Frist unwiderruflich am {deadline}.")
        print("Bei Nichtbeachtung drohen behördliche Sanktionen und Vertriebsverbote.\n")
        print("🔗 [JETZT RECHTLICH ABSICHERN & MELDEN]")

    print("-" * 60 + "\n")


def send_slack_escalation(customer_name, waste_stream, country, deadline):
    print("-" * 60)
    print(f"🚨 [OUTGOING SLACK WEBHOOK] Channel: #support-epr")
    print("-" * 60)

    # Mocking a CRM link generation
    crm_link = f"https://crm.ecosistant.com/customer/{customer_name.replace(' ', '').lower()}"

    payload = f"""{{
  "text": "🚨 *KRITISCHE EPR-FRIST ERREICHT (≤ 3 Tage)* 🚨\\n\\n*Kunde:* {customer_name}\\n*Frist:* {deadline}\\n*Bereich:* {waste_stream} / {country}\\n\\n*Aktion erforderlich:* Bitte Account-Manager prüfen, ob der Kunde Unterstützung benötigt.\\n👉 <{crm_link}|Zum CRM-Eintrag öffnen>"
}}"""
    print(payload)
    print("-" * 60 + "\n")


def update_last_notified(cursor, task_id, today):
    cursor.execute('UPDATE epr_tasks SET last_notified_date = ? WHERE id = ?', (str(today), task_id))
    print(f"💾 [DB SYSTEM] Task ID {task_id} marked as notified on {today}\n\n")


# ==========================================
# 3. CORE LOGIC (PROCESS DESIGN)
# ==========================================
def run_daily_cron(conn):
    print("============================================================")
    print("🟢 STARTING DAILY CRON JOB (05:00 AM)")
    print("============================================================\n")
    cursor = conn.cursor()

    today = datetime.date.today()
    target_30 = today + datetime.timedelta(days=30)
    target_14 = today + datetime.timedelta(days=14)
    target_3 = today + datetime.timedelta(days=3)

    # Fetch relevant data up to 31 days in the future
    max_date = today + datetime.timedelta(days=31)

    cursor.execute('''
        SELECT c.name, t.country, t.waste_stream, t.next_epr_deadline, t.last_notified_date, t.id
        FROM customers c
        JOIN epr_tasks t ON c.id = t.customer_id
        WHERE t.next_epr_deadline <= ?
    ''', (str(max_date),))

    results = cursor.fetchall()

    for row in results:
        customer_name, country, waste_stream, deadline_str, last_notified, task_id = row
        deadline = datetime.datetime.strptime(deadline_str, '%Y-%m-%d').date()

        # State Locking / Anti-Spam Check
        if last_notified == str(today):
            print(f"🛡️ [ANTI-SPAM ACTIVE] Skipping {customer_name} - Already processed today.\n")
            continue

        # Interval Matching
        if deadline == target_30:
            send_email("30_days", customer_name, waste_stream, country, deadline)
            update_last_notified(cursor, task_id, today)

        elif deadline == target_14:
            send_email("14_days", customer_name, waste_stream, country, deadline)
            update_last_notified(cursor, task_id, today)

        elif deadline == target_3:
            send_email("3_days", customer_name, waste_stream, country, deadline)
            send_slack_escalation(customer_name, waste_stream, country, deadline)
            update_last_notified(cursor, task_id, today)

    conn.commit()
    print("============================================================")
    print("🔴 CRON JOB FINISHED")
    print("============================================================")


# ==========================================
# EXECUTION
# ==========================================
if __name__ == "__main__":
    db_connection = setup_database()
    run_daily_cron(db_connection)