# CSpline Activation Server

Flask web application providing license activation and management for CSpline Fusion Suite.

## Features

- **Activation API**: `/activate` endpoint for installer
- **Admin Dashboard**: Web interface to manage licenses
- **Key Generation**: Create new license keys
- **License Management**: View, reset, and track activations
- **Security**: RSA signature-based license tokens

## Quick Deploy to Railway

1. **Create Railway Account**: https://railway.app
2. **Deploy**: Click "Deploy from GitHub" and connect this repository
3. **Set Environment Variables**:
   ```
   ADMIN_PASSWORD=your_secure_password
   RSA_PRIVATE_KEY=your_private_key_pem
   SECRET_KEY=random_secret_key
   ```
4. **Domain**: Railway provides automatic HTTPS domain
5. **Database**: SQLite is created automatically

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run server
python app.py
```

## Production Keys

Generate production RSA keys:

```python
python -c "
from app import rsa, serialization
key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private = key.private_bytes(encoding=serialization.Encoding.PEM, format=serialization.PrivateFormat.PKCS8, encryption_algorithm=serialization.NoEncryption()).decode()
public = key.public_key().public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo).decode()
print('PRIVATE KEY (keep secret):'); print(private)
print('PUBLIC KEY (copy to client):'); print(public)
"
```

## Environment Variables

- `ADMIN_PASSWORD`: Admin interface password (default: admin123)
- `RSA_PRIVATE_KEY`: PEM-encoded RSA private key for signing
- `SECRET_KEY`: Flask session secret
- `PORT`: Server port (default: 5000)

## API Endpoints

### POST /activate
Activate a license key.

**Request:**
```json
{
  "key": "CSPLINE-XXXX-XXXX-XXXX",
  "email": "user@example.com", 
  "name": "John Doe",
  "machine_id": "FA0F9E318E74A0BA"
}
```

**Response (Success):**
```json
{
  "success": true,
  "token": {
    "payload": {
      "product": "CSpline Fusion Suite",
      "edition": "Professional",
      "licensee": {"name": "John Doe", "email": "user@example.com"},
      "machine_id": "FA0F9E318E74A0BA",
      "issued_at": "2025-01-27T10:00:00Z",
      "expires": null
    },
    "sig": "base64_signature"
  }
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "License key already used on another computer"
}
```

### GET /health
Health check endpoint.

## Admin Interface

Access the admin interface at your deployed URL:

1. **Login**: Use ADMIN_PASSWORD
2. **Dashboard**: View activation statistics
3. **License Keys**: Generate, view, and reset keys
4. **Reset Licenses**: Allow license transfers (manual process)

## Security Notes

- Admin password should be strong and unique
- RSA private key must be kept secret
- Use HTTPS in production (automatic on Railway/Render)
- SQLite database is automatically backed up on Railway
- No sensitive data is logged
