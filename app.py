from flask import Flask, render_template_string, request, redirect
import subprocess
from datetime import datetime
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

ips = ["8.8.8.8", "1.1.1.1"]
latency_history = {}

# Ensure static folder exists
if not os.path.exists("static"):
    os.makedirs("static")

def ping(ip):
    try:
        result = subprocess.run(
            ["ping", "-n", "1", ip],  # Windows
            capture_output=True,
            text=True
        )

        if "time=" in result.stdout:
            latency = result.stdout.split("time=")[-1].split("ms")[0]
            return "Active", latency.strip()
        else:
            return "Down", "N/A"

    except:
        return "Error", "N/A"


@app.route("/")
def home():
    data = []

    for ip in ips:
        status, latency = ping(ip)

        # ALERT
        if status == "Down":
            print(f"⚠️ ALERT: {ip} is DOWN!")

        # LOGGING
        with open("log.txt", "a") as f:
            f.write(f"{datetime.now()} - {ip} - {status} - {latency} ms\n")

        # LATENCY TRACKING
        if ip not in latency_history:
            latency_history[ip] = []

        if latency != "N/A":
            latency_history[ip].append(float(latency))

        latency_history[ip] = latency_history[ip][-10:]

        data.append({
            "ip": ip,
            "status": status,
            "latency": latency,
            "time": datetime.now().strftime("%H:%M:%S")
        })

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Network Monitor</title>
        <meta http-equiv="refresh" content="5">

        <style>
            body {
                font-family: Arial;
                background: linear-gradient(to right, #1e3c72, #2a5298);
                color: white;
                text-align: center;
            }

            h1 {
                margin-top: 30px;
            }

            form {
                margin-top: 20px;
            }

            input {
                padding: 10px;
                border-radius: 5px;
                border: none;
            }

            button {
                padding: 10px 15px;
                background: #00c6ff;
                border: none;
                color: white;
                border-radius: 5px;
                cursor: pointer;
            }

            table {
                margin: 30px auto;
                border-collapse: collapse;
                width: 70%;
                background: white;
                color: black;
                border-radius: 10px;
                overflow: hidden;
            }

            th, td {
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }

            th {
                background-color: #2a5298;
                color: white;
            }

            .active {
                color: green;
                font-weight: bold;
            }

            .down {
                color: red;
                font-weight: bold;
            }

            .card {
                background: white;
                color: black;
                padding: 15px;
                border-radius: 10px;
                display: inline-block;
                margin: 10px;
            }

            a {
                text-decoration: none;
                color: blue;
                font-weight: bold;
            }
        </style>
    </head>

    <body>

        <h1>🌐 Network Monitoring Dashboard</h1>

        <!-- Add IP -->
        <form action="/add" method="post">
            <input type="text" name="ip" placeholder="Enter IP address" required>
            <button type="submit">Add IP</button>
        </form>

        <!-- Stats -->
        <div class="card">
            <h3>Total Devices</h3>
            <p>{{data|length}}</p>
        </div>

        <!-- Table -->
        <table>
            <tr>
                <th>IP Address</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Last Checked</th>
                <th>Graph</th>
            </tr>

            {% for item in data %}
            <tr>
                <td>{{item.ip}}</td>
                <td class="{{ 'active' if item.status == 'Active' else 'down' }}">
                    {{item.status}}
                </td>
                <td>{{item.latency}} ms</td>
                <td>{{item.time}}</td>
                <td>
                    <a href="/graph/{{item.ip}}" target="_blank">📊 View</a>
                </td>
            </tr>
            {% endfor %}
        </table>

    </body>
    </html>
    """

    return render_template_string(html, data=data)


@app.route("/add", methods=["POST"])
def add_ip():
    new_ip = request.form.get("ip")
    if new_ip and new_ip not in ips:
        ips.append(new_ip)
    return redirect("/")


@app.route("/graph/<ip>")
def graph(ip):
    if ip not in latency_history or len(latency_history[ip]) == 0:
        return "No data yet"

    plt.figure()
    plt.plot(latency_history[ip])
    plt.title(f"Latency for {ip}")
    plt.xlabel("Time")
    plt.ylabel("Latency (ms)")

    filepath = f"static/{ip}.png"
    plt.savefig(filepath)
    plt.close()

    return f'<img src="/{filepath}">'


if __name__ == "__main__":
    app.run(debug=True)