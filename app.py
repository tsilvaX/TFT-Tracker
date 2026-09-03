from flask import Flask, render_template, jsonify
from tft_tracker import get_stats, get_avg_placement

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    return jsonify({
        'top4_rate': round(get_stats(), 1),
        'avg_placement': round(get_avg_placement(), 1)
    })

if __name__ == "__main__":
    app.run(debug=True)