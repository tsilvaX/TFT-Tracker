import requests
from flask import Flask, render_template, jsonify, request
from tft_tracker import (
    analyze_selection,
    calculate_dashboard_stats,
    calculate_tftacademy_comp_performance,
    get_tftacademy_comps,
)

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    riot_id = request.args.get('riot_id') or None
    set_number = request.args.get('set') or None
    patch = request.args.get('patch') or None
    limit = request.args.get('limit') or None
    match_count = request.args.get('match_count') or None
    refresh = request.args.get('refresh') == '1'
    current_only = request.args.get('current_only', '0') == '1'

    try:
        return jsonify(
            calculate_dashboard_stats(
                riot_id=riot_id,
                set_number=set_number,
                patch=patch,
                limit=limit,
                match_count=match_count,
                current_only=current_only,
                refresh=refresh,
            )
        )
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else 502
        if status_code in (401, 403):
            message = 'Riot API rejected the API key. Generate a fresh development key and update .env.'
        elif status_code == 404:
            message = 'Riot ID not found.'
        else:
            message = 'Riot API request failed.'

        return jsonify({'error': message, 'status_code': status_code}), status_code
    except requests.RequestException:
        return jsonify({'error': 'Could not reach the Riot API.'}), 502
    except RuntimeError as error:
        return jsonify({'error': str(error)}), 500


@app.route('/api/comps')
def comps():
    refresh = request.args.get('refresh') == '1'

    try:
        return jsonify(get_tftacademy_comps(refresh=refresh))
    except requests.RequestException:
        return jsonify({'error': 'Could not load TFTAcademy comps.'}), 502


@app.route('/api/analysis')
def analysis():
    riot_id = request.args.get('riot_id') or None
    units = _csv_values(request.args.get('units'))
    traits = _csv_values(request.args.get('traits'))
    comp_units = _csv_values(request.args.get('comp_units'))
    set_number = request.args.get('set') or None
    patch = request.args.get('patch') or None
    match_count = request.args.get('match_count') or None

    if not riot_id:
        return jsonify({'error': 'Enter a Riot ID in the format GameName#TAG.'}), 400

    try:
        return jsonify(
            analyze_selection(
                riot_id=riot_id,
                units=units,
                traits=traits,
                comp_units=comp_units,
                set_number=set_number,
                patch=patch,
                match_count=match_count,
            )
        )
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else 502
        return jsonify({'error': 'Riot API request failed.', 'status_code': status_code}), status_code
    except requests.RequestException:
        return jsonify({'error': 'Could not reach the Riot API.'}), 502
    except RuntimeError as error:
        return jsonify({'error': str(error)}), 500


@app.route('/api/academy-performance')
def academy_performance():
    riot_id = request.args.get('riot_id') or None
    set_number = request.args.get('set') or None
    patch = request.args.get('patch') or None
    limit = request.args.get('limit') or None
    match_count = request.args.get('match_count') or None
    refresh_comps = request.args.get('refresh_comps') == '1'
    current_only = request.args.get('current_only', '0') == '1'

    if not riot_id:
        return jsonify({'error': 'Enter a Riot ID in the format GameName#TAG.'}), 400

    try:
        return jsonify(
            calculate_tftacademy_comp_performance(
                riot_id=riot_id,
                set_number=set_number,
                patch=patch,
                limit=limit,
                match_count=match_count,
                current_only=current_only,
                refresh_comps=refresh_comps,
            )
        )
    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except requests.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else 502
        if status_code in (401, 403):
            message = 'Riot API rejected the API key. Generate a fresh development key and update .env.'
        elif status_code == 404:
            message = 'Riot ID not found.'
        else:
            message = 'Riot API request failed.'

        return jsonify({'error': message, 'status_code': status_code}), status_code
    except requests.RequestException:
        return jsonify({'error': 'Could not reach the Riot API or TFTAcademy.'}), 502
    except RuntimeError as error:
        return jsonify({'error': str(error)}), 500


def _csv_values(value):
    if not value:
        return []

    return [part.strip() for part in value.split(',') if part.strip()]

if __name__ == "__main__":
    app.run(debug=True)
