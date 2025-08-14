# CSpline Activation Server - Deployment Guide

## 🚀 Quick Deploy to Railway (Recommended)

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub or email
3. Free tier: 500 hours/month, $0 cost for small usage

### Step 2: Deploy the Server
1. **Create New Project** in Railway dashboard
2. **Deploy from Local Directory**: Upload the `activation_server` folder
   - OR **Connect GitHub**: Push to repo and deploy from GitHub
3. **Auto-Deploy**: Railway detects Flask app automatically

### Step 3: Set Environment Variables
In Railway dashboard → Variables tab:

```
ADMIN_PASSWORD=your_secure_admin_password_123
SECRET_KEY=random_string_here_32_chars_min
FLASK_ENV=production
```

### Step 4: Get Your Server URL
- Railway provides automatic HTTPS domain like: `https://cspline-activation-xyz.up.railway.app`
- Custom domain optional: `activate.cspline.com`

### Step 5: Update Client Configuration
Update in `Installer/activation_dialog.py`:
```python
ACTIVATION_SERVER_URL = "https://your-railway-domain.up.railway.app/activate"
```

---

## 🛠 Alternative: Deploy to Render

### Step 1: Create Render Account
1. Go to https://render.com
2. Free tier available

### Step 2: Deploy Web Service
1. **New Web Service** from Git repository
2. **Build Command**: `pip install -r requirements.txt`
3. **Start Command**: `gunicorn app:app`
4. **Environment**: Python 3

### Step 3: Set Environment Variables
Same as Railway above.

---

## 🔑 Generate Production RSA Keys

**Important**: Generate new keys for production!

```bash
# In activation_server directory
python -c "
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Generate key pair
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

# Get PEM strings
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode()

public_pem = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

print('=== PRIVATE KEY (Server Environment Variable) ===')
print(private_pem)
print('=== PUBLIC KEY (Copy to license/crypto_utils.py) ===') 
print(public_pem)
"
```

**Security**: 
- Keep private key in server environment variables only
- Copy public key to `license/crypto_utils.py` in client
- Never commit private key to version control

---

## 📊 Admin Interface Usage

### Login
- URL: `https://your-domain/`
- Password: Your `ADMIN_PASSWORD`

### Generate License Keys
1. **Dashboard** → "Generate New Keys"
2. Choose quantity (1-100)
3. Add notes for tracking
4. Keys format: `CSPLINE-XXXX-XXXX-XXXX`

### Manage Activations
1. **License Keys** page shows all keys
2. View activation status and user info
3. **Reset** used keys for license transfers
4. Track activation history

### Monitor Usage
- Dashboard shows activation statistics
- Recent activations list
- Usage patterns and trends

---

## 🔧 Production Configuration

### Required Environment Variables
```bash
ADMIN_PASSWORD=secure_random_password_here
RSA_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
SECRET_KEY=flask_session_secret_32_chars_min
FLASK_ENV=production
```

### Optional Configuration
```bash
PORT=5000  # Default port (Railway/Render handle this)
```

### Security Checklist
- ✅ Strong admin password (12+ characters)
- ✅ Unique RSA key pair for production
- ✅ HTTPS enabled (automatic on Railway/Render)
- ✅ Private key in environment variables only
- ✅ Database backups (automatic on Railway)

---

## 🧪 Testing Deployment

### Test the API
```bash
curl -X POST https://your-domain/activate \
  -H "Content-Type: application/json" \
  -d '{
    "key": "CSPLINE-TEST-KEY1-2024",
    "email": "test@example.com",
    "name": "Test User", 
    "machine_id": "FA0F9E318E74A0BA"
  }'
```

### Test Admin Interface
1. Visit: `https://your-domain/`
2. Login with admin password
3. Generate test keys
4. Verify key management works

---

## 💰 Hosting Costs

### Railway (Recommended)
- **Free**: 500 hours/month
- **Pro**: $5/month for unlimited
- **Features**: Auto-scaling, backups, monitoring

### Render
- **Free**: 750 hours/month (sleeps after 15min idle)
- **Starter**: $7/month for always-on
- **Features**: Auto-SSL, GitHub integration

### Estimated Monthly Costs
- **Low usage** (< 100 activations/month): **FREE**
- **Medium usage** (< 1000 activations/month): **$5-7/month**
- **High usage**: Auto-scales, minimal cost increase

---

## 🚨 Production Checklist

- [ ] Deploy to Railway/Render
- [ ] Generate production RSA keys
- [ ] Set strong admin password
- [ ] Update client activation URL
- [ ] Test activation flow end-to-end
- [ ] Set up custom domain (optional)
- [ ] Test license key generation
- [ ] Test key reset functionality
- [ ] Document admin procedures

**Ready to go live!** 🎉
