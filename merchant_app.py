from flask import Flask, request, jsonify, send_from_directory
import random
import time
from datetime import datetime
import os

app = Flask(__name__, static_folder="static")

# --- In-Memory State for Demo ---
merchant_stats = {
    "history": [random.randint(100, 500) for _ in range(20)],
    "credit_scores": [720],
    "threshold": 3.0  # 3x deviation from mean
}

def calculate_score(upi_vol, supplier_consistency, footfall, event_impact):
    """
    Simplified scoring logic:
    - UPI Volume: 40%
    - Supplier consistency: 30%
    - Footfall: 20%
    - Local events: 10%
    """
    score = (upi_vol * 0.05) + (supplier_consistency * 2) + (footfall * 0.5) + (event_impact * 10)
    return min(max(int(score + 300), 300), 900)

def detect_anomaly(current_tx):
    avg = sum(merchant_stats["history"]) / len(merchant_stats["history"])
    deviation = current_tx / avg
    is_fraud = deviation > merchant_stats["threshold"]
    return is_fraud, round(deviation, 2)

@app.route('/')
def index():
    return send_from_directory('static', 'merchant_dashboard.html')

@app.route('/api/score', methods=['POST'])
def get_score():
    data = request.json or {}
    
    # Inputs
    upi_vol = data.get('upi_vol', random.randint(2000, 8000))
    supplier_score = data.get('supplier_score', random.randint(60, 100))
    footfall = data.get('footfall', random.randint(100, 500))
    event_impact = data.get('event_impact', random.randint(0, 10))
    current_tx = data.get('current_tx', random.randint(100, 600))

    # Logic
    score = calculate_score(upi_vol, supplier_score, footfall, event_impact)
    is_fraud, deviation = detect_anomaly(current_tx)
    
    # Update state
    merchant_stats["history"].append(current_tx)
    if len(merchant_stats["history"]) > 30: merchant_stats["history"].pop(0)
    merchant_stats["credit_scores"].append(score)
    if len(merchant_stats["credit_scores"]) > 30: merchant_stats["credit_scores"].pop(0)

    return jsonify({
        "status": "success",
        "data": {
            "credit_score": score,
            "fraud_alert": is_fraud,
            "deviation": deviation,
            "current_tx": current_tx,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        }
    })

@app.route('/api/dashboard-init')
def dashboard_init():
    return jsonify({
        "history": merchant_stats["history"],
        "credit_scores": merchant_stats["credit_scores"],
        "merchant_name": "Suresh Kirana Store",
        "location": "Dharavi, Mumbai"
    })

if __name__ == '__main__':
    print("Merchant Credit Engine running at http://127.0.0.1:5001")
    app.run(debug=True, port=5001)
