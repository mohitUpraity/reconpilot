import hmac, hashlib, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from api.webhooks import verify_razorpay_signature

def test_valid_signature():
    body=b'{"event":"payment.captured"}'
    secret="secret"
    sig=hmac.new(secret.encode(),body,hashlib.sha256).hexdigest()
    assert verify_razorpay_signature(body,sig,secret)

def test_invalid_signature():
    assert not verify_razorpay_signature(b'{"event":"payment.captured"}',"bad","secret")
