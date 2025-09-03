
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import os

app = Flask(__name__)
app.secret_key = "mysecretkey"
bcrypt = Bcrypt(app)

# ====== MongoDB Connection with fallback and error handling ======
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/travel_booking")
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()  # Force connection
    db = client["travel_booking"]
    users_collection = db["users"]
    messages_collection = db["messages"]
    db_connected = True
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    db = None
    users_collection = None
    messages_collection = None
    db_connected = False


# ====== ROUTES ======

@app.route("/")
def index():
    if not db_connected:
        return (
            "<h2>Database connection error.</h2>"
            "<p>Please check your MongoDB connection string.</p>"
            "<p>If deploying on Render, set the MONGO_URI environment variable to your MongoDB Atlas connection string.</p>"
            "<p>If running locally, ensure MongoDB is running and accessible at the URI specified.</p>", 500
        )
    if "user" in session:
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    if not db_connected:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for("index"))
    username = request.form["username"]
    password = request.form["password"]

    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        session["user"] = username
        flash("Login successful!", "success")
        return redirect(url_for("home"))
    else:
        flash("Invalid username or password", "danger")
        return redirect(url_for("index"))

@app.route("/signup", methods=["POST"])
def signup():
    if not db_connected:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for("index"))
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        flash("⚠ Username already exists, choose another!", "warning")
        return redirect(url_for("index"))
    else:
        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
        users_collection.insert_one({
            "username": username,
            "email": email,
            "password": hashed_password
        })
        flash("✅ Signup successful! Please login.", "success")
        return redirect(url_for("index"))

@app.route("/home")
def home():
    if not db_connected:
        return "<h2>Database connection error. Please contact support.</h2>", 500
    if "user" not in session:
        flash("⚠ Please login first!", "danger")
        return redirect(url_for("index"))
    return render_template("index.html", username=session["user"])

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if not db_connected:
        flash("Database connection error. Please try again later.", "danger")
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        message = request.form["message"]

        messages_collection.insert_one({
            "name": name,
            "email": email,
            "message": message
        })

        flash("✅ Your message has been submitted successfully!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ====== MAIN ======
if __name__ == "__main__":   # ✅ Corrected
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
