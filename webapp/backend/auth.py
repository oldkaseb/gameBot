# webapp/backend/auth.py
import hashlib
import hmac
import json
from urllib.parse import parse_qsl
from fastapi import HTTPException

BOT_TOKEN = "توکن_ربات_خود_را_اینجا_بگذارید"

def validate_init_data(init_data: str) -> dict:
    try:
        parsed_data = dict(parse_qsl(init_data))
        if "hash" not in parsed_data:
            raise HTTPException(status_code=401, detail="Hash missing")
            
        hash_val = parsed_data.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if calculated_hash != hash_val:
            raise HTTPException(status_code=403, detail="Invalid initData")
            
        return json.loads(parsed_data.get("user", "{}"))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid initData format")
