# ============================================
# PART 1: Cloud Webhook Receiver (Flask)
# Deploy this to Heroku, Railway, or any cloud platform
# File: webhook_server.py
# ============================================

from flask import Flask, request, jsonify
from datetime import datetime
import json

app = Flask(__name__)

# In-memory queue (use Redis for production)
command_queue = []

@app.route('/webhook', methods=['POST'])
def tekmetric_webhook():
    """Receives webhooks from Tekmetric"""
    try:
        data = request.json
        print(f"[{datetime.now()}] Received webhook: {json.dumps(data)}")
        
        # Check if paymentType.code is "CASH"
        if 'paymentType' in data:
            payment_type = data['paymentType']
            if payment_type.get('code') == 'CASH':
                # Add command to queue
                command_queue.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': '1',
                    'processed': False
                })
                print(f"[{datetime.now()}] CASH payment detected - command queued")
        
        return jsonify({'status': 'success'}), 200
    
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/poll', methods=['GET'])
def poll_commands():
    """Local app polls this endpoint for pending commands"""
    try:
        # Get unprocessed commands
        pending = [cmd for cmd in command_queue if not cmd['processed']]
        
        if pending:
            # Mark as processed
            for cmd in pending:
                cmd['processed'] = True
            
            return jsonify({
                'status': 'success',
                'commands': pending
            }), 200
        else:
            return jsonify({
                'status': 'success',
                'commands': []
            }), 200
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'queue_size': len(command_queue)
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
