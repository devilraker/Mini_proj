from flask import Flask, render_template, request, flash

app = Flask(__name__)
app.secret_key = "manblahblah"

# Main page - the control panel with 3 buttons
@app.route("/")
def index():
    return render_template("index.html")

# Fan control page
@app.route("/fan")
def fan():
    return render_template("fan.html")

# Light control page
@app.route("/light")
def light():
    return render_template("light.html")

# Bed angle control page
@app.route("/bed")
def bed():
    return render_template("bed.html")

if __name__ == "__main__":
    app.run(debug=True)