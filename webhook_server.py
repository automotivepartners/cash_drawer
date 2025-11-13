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
        # Log raw request for debugging
        print(f"[{datetime.now()}] ===== WEBHOOK RECEIVED =====")
        print(f"Headers: {dict(request.headers)}")
        print(f"Raw data: {request.get_data(as_text=True)}")
        
        data = request.json
        print(f"Parsed JSON: {json.dumps(data, indent=2)}")
        
        # Check if paymentType.code is "CASH"
        if 'paymentType' in data:
            payment_type = data['paymentType']
            print(f"Found paymentType: {payment_type}")
            
            if payment_type.get('code') == 'CASH':
                # Add command to queue
                command_queue.append({
                    'timestamp': datetime.now().isoformat(),
                    'command': '1',
                    'processed': False
                })
                print(f"[{datetime.now()}] ✓ CASH PAYMENT DETECTED - COMMAND QUEUED!")
                print(f"Queue now has {len(command_queue)} items")
            else:
                print(f"Payment code is '{payment_type.get('code')}', not CASH")
        else:
            print("WARNING: No 'paymentType' field found in webhook data")
        
        print(f"===== END WEBHOOK =====\n")
        return jsonify({'status': 'success', 'received': True}), 200
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
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

@app.route('/', methods=['GET'])
def home():
    """Root endpoint"""
    return jsonify({
        'service': 'Tekmetric Webhook Receiver',
        'status': 'running',
        'endpoints': {
            'webhook': '/webhook (POST)',
            'poll': '/poll (GET)',
            'health': '/health (GET)'
        }
    }), 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
