import os
from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        {
            "application": "Jenkins Production CI/CD Demo",
            "version": "1.0.0",
            "status": "running",
        }
    )


@app.route("/health")
def health():
    if os.getenv("FORCE_HEALTH_FAILURE", "").lower() == "true":
        return jsonify({"status": "unhealthy"}), 500

    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
