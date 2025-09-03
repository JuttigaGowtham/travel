from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_bcrypt import Bcrypt
from pymongo import MongoClient
import os

app = Flask(__name__)   # ✅ Corrected
app.secret_key = "mysecretkey"

# ====== MongoDB Connection ======
from pymongo import MongoClient

MONGO_URI = os.environ.get("MONGO_URI")  # set this in Render environment variables
client = MongoClient(MONGO_URI)
db = client["travel_booking"]
users_collection = db["users"]
messages_collection = db["messages"]


# ====== ROUTES ======

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
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
    if "user" not in session:
        flash("⚠ Please login first!", "danger")
        return redirect(url_for("index"))
    return render_template("index.html", username=session["user"])

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact", methods=["GET", "POST"])
def contact():
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
