from flask import Flask, render_template, request, redirect, flash
import sqlite3
import time
import os

app = Flask(__name__)
app.secret_key = "super_secret_duco_key"  # Required for alert messages

# --- DATABASE SETUP ---
DB_FILE = "faucet_list.db"

def init_db():
    """Creates a local lightweight database table if it doesn't exist yet."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- WEB APP ROUTES ---

@app.route("/", methods=["GET", "POST"])
def faucet_home():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    if request.method == "POST":
        # Pull what the user typed into the HTML input box
        input_username = request.form.get("username", "").strip()

        if not input_username:
            flash("❌ Please enter a valid Duino-Coin username!", "error")
        else:
            current_time = time.time()
            
            # Anti-Spam Check: Has this user claimed in the last 12 hours?
            twelve_hours_ago = current_time - (12 * 3600)
            cursor.execute("SELECT * FROM claims WHERE username = ? AND timestamp > ?", (input_username, twelve_hours_ago))
            existing_claim = cursor.fetchone()

            if existing_claim:
                flash("⏳ Cooldown active! You can only claim free DUCO once every 12 hours.", "warning")
            else:
                # Save the user cleanly into the database list
                cursor.execute("INSERT INTO claims (username, timestamp) VALUES (?, ?)", (input_username, current_time))
                conn.commit()
                flash(f"🎉 Success! Your username '{input_username}' has been queued for DUCO payout!", "success")

        return redirect("/")

    # GET Request: Fetch the absolute latest users queued for payouts to show on screen
    cursor.execute("SELECT username, datetime(timestamp, 'unixepoch', 'localtime') FROM claims ORDER BY id DESC")
    all_users = cursor.fetchall()
    conn.close()

    return render_template("index.html", users=all_users)

if __name__ == "__main__":
    app.run(debug=True)
