import os
import sys

def require_env(var_name):
    value = os.getenv(var_name)
    if value is None or value == '':
        print(f"[ERROR] Missing required environment variable: {var_name}", flush=True, file=sys.stderr)
        sys.exit(1)
    print(f"[DEBUG] Loaded {var_name}: {value}", flush=True, file=sys.stderr)
    return value

DEEPL_API_KEY = require_env("DEEPL_API_KEY")
ADMIN_PASSWORD = require_env("ADMIN_PASSWORD")
OPENAI_API_KEY = require_env("OPENAI_API_KEY")
