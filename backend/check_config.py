from config import config

print("=== AMap Configuration Check ===")
print(f"API Key: {config.AMAP_API_KEY[:30]}...")
print(f"API Key Length: {len(config.AMAP_API_KEY)}")
print(f"Is Default Key: {config.AMAP_API_KEY == 'YOUR_AMAP_API_KEY_HERE'}")
print(f"Security Key: {config.AMAP_SECURITY_KEY[:30]}...")
