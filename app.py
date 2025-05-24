# app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
from collections import defaultdict
import time

app = Flask(__name__)
CORS(app)

# Store active peers
peers = {}
peer_last_seen = {}

@app.route('/register', methods=['POST'])
def register_peer():
    peer_id = str(uuid.uuid4())
    peers[peer_id] = {'id': peer_id, 'offer': None}
    peer_last_seen[peer_id] = time.time()
    return jsonify({'peer_id': peer_id})

@app.route('/discover', methods=['GET'])
def discover_peers():
    # Clean up old peers
    current_time = time.time()
    for peer_id in list(peers.keys()):
        if current_time - peer_last_seen.get(peer_id, 0) > 60:  # 60 seconds timeout
            del peers[peer_id]
            del peer_last_seen[peer_id]
    
    active_peers = [{'id': pid} for pid in peers.keys()]
    return jsonify({'peers': active_peers})

@app.route('/signal/<peer_id>', methods=['POST'])
def handle_signal(peer_id):
    if peer_id not in peers:
        return jsonify({'error': 'Peer not found'}), 404
    
    data = request.json
    signal_type = data.get('type')
    signal_data = data.get('data')
    target_peer = data.get('target_peer')
    
    # Update peer last seen time
    peer_last_seen[peer_id] = time.time()
    
    if signal_type == 'offer':
        peers[peer_id]['offer'] = signal_data
        return jsonify({'status': 'offer stored'})
    elif signal_type == 'answer' and target_peer in peers:
        # Store answer with the offering peer
        peers[target_peer]['answer'] = signal_data
        return jsonify({'status': 'answer stored'})
    elif signal_type == 'candidate' and target_peer in peers:
        # Forward ICE candidate
        if 'candidates' not in peers[target_peer]:
            peers[target_peer]['candidates'] = []
        peers[target_peer]['candidates'].append(signal_data)
        return jsonify({'status': 'candidate stored'})
    
    return jsonify({'error': 'Invalid signal type'}), 400

@app.route('/get_offer/<peer_id>', methods=['GET'])
def get_offer(peer_id):
    if peer_id not in peers:
        return jsonify({'error': 'Peer not found'}), 404
    return jsonify({'offer': peers[peer_id].get('offer')})

@app.route('/get_answer/<peer_id>', methods=['GET'])
def get_answer(peer_id):
    if peer_id not in peers:
        return jsonify({'error': 'Peer not found'}), 404
    return jsonify({'answer': peers[peer_id].get('answer')})

@app.route('/get_candidates/<peer_id>', methods=['GET'])
def get_candidates(peer_id):
    if peer_id not in peers:
        return jsonify({'error': 'Peer not found'}), 404
    return jsonify({'candidates': peers[peer_id].get('candidates', [])})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)