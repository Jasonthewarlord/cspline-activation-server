"""
CSpline Activation Server
Flask web application providing activation API and admin interface.
"""

import os
import json
import sqlite3
import secrets
import datetime
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash, session
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import base64
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

# Database file
DATABASE = 'cspline_licenses.db'

# RSA Keys (will be loaded from environment/files)
PRIVATE_KEY = None
PUBLIC_KEY = None

def init_database():
    """Initialize the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS license_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT UNIQUE NOT NULL,
            email TEXT,
            name TEXT,
            machine_id TEXT,
            claimed_at TIMESTAMP,
            status TEXT DEFAULT 'unused',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    ''')
    
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_key TEXT NOT NULL,
            email TEXT NOT NULL,
            name TEXT NOT NULL,
            machine_id TEXT NOT NULL,
            activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ip_address TEXT,
            user_agent TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def load_rsa_keys():
    """Load RSA keys from environment or generate for development."""
    global PRIVATE_KEY, PUBLIC_KEY
    
    try:
        # Try to load from environment
        private_key_pem = os.environ.get('RSA_PRIVATE_KEY')
        
        if private_key_pem:
            PRIVATE_KEY = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None
            )
            PUBLIC_KEY = PRIVATE_KEY.public_key()
        else:
            # Generate development keys
            print("No RSA keys found in environment. Generating development keys...")
            PRIVATE_KEY = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048
            )
            PUBLIC_KEY = PRIVATE_KEY.public_key()
            
            # Print public key for client integration
            public_pem = PUBLIC_KEY.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode('utf-8')
            
            print("=== DEVELOPMENT RSA PUBLIC KEY ===")
            print(public_pem)
            print("=== Copy this to crypto_utils.py ===")
            
    except Exception as e:
        print(f"Error loading RSA keys: {e}")
        PRIVATE_KEY = None
        PUBLIC_KEY = None

def sign_license_payload(payload):
    """Sign a license payload with the private key."""
    if not PRIVATE_KEY:
        return None
        
    try:
        # Convert payload to canonical JSON
        payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
        payload_bytes = payload_json.encode('utf-8')
        
        # Sign the payload
        signature = PRIVATE_KEY.sign(
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return base64.b64encode(signature).decode('utf-8')
        
    except Exception as e:
        print(f"Error signing payload: {e}")
        return None

def generate_license_key():
    """Generate a new license key."""
    return f"CSPLINE-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"

@app.route('/')
def index():
    """Main admin dashboard."""
    if 'authenticated' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect(DATABASE)
    
    # Get stats
    total_keys = conn.execute('SELECT COUNT(*) FROM license_keys').fetchone()[0]
    used_keys = conn.execute('SELECT COUNT(*) FROM license_keys WHERE status = "claimed"').fetchone()[0]
    total_activations = conn.execute('SELECT COUNT(*) FROM activations').fetchone()[0]
    
    # Get recent activations
    recent_activations = conn.execute('''
        SELECT email, name, machine_id, activated_at 
        FROM activations 
        ORDER BY activated_at DESC 
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('dashboard.html', 
                         total_keys=total_keys,
                         used_keys=used_keys,
                         unused_keys=total_keys-used_keys,
                         total_activations=total_activations,
                         recent_activations=recent_activations)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page."""
    if request.method == 'POST':
        password = request.form.get('password')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        if password == admin_password:
            session['authenticated'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid password', 'error')
    
    return render_template('login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout."""
    session.pop('authenticated', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/keys')
def manage_keys():
    """License key management page."""
    if 'authenticated' not in session:
        return redirect(url_for('admin_login'))
    
    conn = sqlite3.connect(DATABASE)
    keys = conn.execute('''
        SELECT id, license_key, email, name, machine_id, status, claimed_at, created_at
        FROM license_keys 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    return render_template('keys.html', keys=keys)

@app.route('/admin/generate_keys', methods=['POST'])
def generate_keys():
    """Generate new license keys."""
    if 'authenticated' not in session:
        return redirect(url_for('admin_login'))
    
    try:
        count = int(request.form.get('count', 1))
        notes = request.form.get('notes', '')
        
        conn = sqlite3.connect(DATABASE)
        for _ in range(count):
            key = generate_license_key()
            conn.execute(
                'INSERT INTO license_keys (license_key, notes) VALUES (?, ?)',
                (key, notes)
            )
        conn.commit()
        conn.close()
        
        flash(f'Generated {count} new license keys', 'success')
        
    except Exception as e:
        flash(f'Error generating keys: {e}', 'error')
    
    return redirect(url_for('manage_keys'))

@app.route('/admin/reset_license', methods=['POST'])
def reset_license():
    """Reset a license key to unused status."""
    if 'authenticated' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        key_id = request.form.get('key_id')
        
        conn = sqlite3.connect(DATABASE)
        conn.execute('''
            UPDATE license_keys 
            SET status = 'unused', email = NULL, name = NULL, 
                machine_id = NULL, claimed_at = NULL 
            WHERE id = ?
        ''', (key_id,))
        conn.commit()
        conn.close()
        
        flash('License key reset successfully', 'success')
        
    except Exception as e:
        flash(f'Error resetting license: {e}', 'error')
    
    return redirect(url_for('manage_keys'))

@app.route('/activate', methods=['POST'])
def activate():
    """Main activation endpoint for the installer."""
    try:
        # Parse request
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Invalid request format'}), 400
        
        key = data.get('key', '').strip()
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        machine_id = data.get('machine_id', '').strip()
        
        # Validate input
        if not all([key, email, name, machine_id]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Check database
        conn = sqlite3.connect(DATABASE)
        
        # Check if key exists and status
        key_record = conn.execute(
            'SELECT id, status, machine_id FROM license_keys WHERE license_key = ?',
            (key,)
        ).fetchone()
        
        if not key_record:
            conn.close()
            return jsonify({'success': False, 'error': 'Invalid license key'}), 400
        
        key_id, status, claimed_machine_id = key_record
        
        # Check if key is already used by different machine
        if status == 'claimed' and claimed_machine_id != machine_id:
            conn.close()
            return jsonify({'success': False, 'error': 'License key already used on another computer'}), 400
        
        # If same machine, allow reactivation
        if status == 'claimed' and claimed_machine_id == machine_id:
            print(f"Reactivation for machine {machine_id}")
        else:
            # Claim the key
            conn.execute('''
                UPDATE license_keys 
                SET status = 'claimed', email = ?, name = ?, machine_id = ?, claimed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (email, name, machine_id, key_id))
        
        # Log activation
        conn.execute('''
            INSERT INTO activations (license_key, email, name, machine_id, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (key, email, name, machine_id, request.remote_addr, request.headers.get('User-Agent', '')))
        
        conn.commit()
        conn.close()
        
        # Create license token
        payload = {
            "product": "CSpline Fusion Suite",
            "edition": "Professional",
            "licensee": {
                "name": name,
                "email": email
            },
            "machine_id": machine_id,
            "issued_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "expires": None
        }
        
        # Sign the payload
        signature = sign_license_payload(payload)
        if not signature:
            return jsonify({'success': False, 'error': 'Server signing error'}), 500
        
        token = {
            "payload": payload,
            "sig": signature
        }
        
        return jsonify({
            'success': True,
            'token': token
        })
        
    except Exception as e:
        print(f"Activation error: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'CSpline Activation Server'})

# Initialize on startup
init_database()
load_rsa_keys()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)
