from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import os

# ====== Flask Setup ======
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "defaultsecret")  # ✅ Use env var in production

# ====== Extensions ======
bcrypt = Bcrypt(app)

# ====== MongoDB Connection ======
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
try:
    client = MongoClient(MONGO_URI)
    db = client["travel_booking"]
    users_collection = db["users"]
    messages_collection = db["messages"]
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")
    raise

# ====== ROUTES ======

@app.route("/")
def index():
    """Login page"""
    if "user" in session:
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    """User login"""
    username = request.form.get("username")
    password = request.form.get("password")

    user = users_collection.find_one({"username": username})
    if user and bcrypt.check_password_hash(user["password"], password):
        session["user"] = username
        flash("✅ Login successful!", "success")
        return redirect(url_for("home"))
    else:
        flash("❌ Invalid username or password", "danger")
        return redirect(url_for("index"))

@app.route("/signup", methods=["POST"])
def signup():
    """User signup"""
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    existing_user = users_collection.find_one({"username": username})
    if existing_user:
        flash("⚠ Username already exists, choose another!", "warning")
        return redirect(url_for("index"))
    
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
    """Home page (requires login)"""
    if "user" not in session:
        flash("⚠ Please login first!", "danger")
        return redirect(url_for("index"))
    return render_template("index.html", username=session["user"])

@app.route("/about")
def about():
    """About page"""
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Contact page (stores messages in DB)"""
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

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
    """Logout user"""
    session.pop("user", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))

# ====== MAIN ======
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # ✅ Render provides PORT
    app.run(host="0.0.0.0", port=port)
