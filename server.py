#!/usr/bin/env python3
from flask import Flask, request, jsonify
import logging, os, time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

INSTALL_DIR   = "/opt/mtunnel"
TOKEN_FILE    = os.path.join(INSTALL_DIR, ".token")
CONFIG_FILE   = os.path.join(INSTALL_DIR, ".config")

# Cache expire time tính bằng giây (mặc định 1h)
CACHE_TTL = 3600

def get_token():
    try:
        with open(TOKEN_FILE, "r") as f:
            return f.read().strip()
    except:
        return ""

def get_package():
    try:
        with open(CONFIG_FILE, "r") as f:
            for line in f:
                if line.startswith("PACKAGE="):
                    return line.strip().split("=", 1)[1]
    except:
        return ""

@app.route("/api/verify", methods=["POST"])
def verify():
    data  = request.get_json(force=True, silent=True) or {}
    token = data.get("token", "")
    pkg   = data.get("pkg",   "")
    ip    = request.remote_addr

    app.logger.info(f"Request from {ip} | pkg={pkg} | token={token[:8]}...")

    valid_token   = get_token()
    valid_package = get_package()

    if not valid_token:
        app.logger.warning("Token chua duoc thiet lap!")
        return jsonify({"valid": False, "reason": "server_not_configured"})

    if pkg != valid_package:
        app.logger.warning(f"Wrong package: {pkg}")
        return jsonify({"valid": False, "reason": "wrong_package"})

    if token == valid_token:
        expire_at = int(time.time()) + CACHE_TTL
        app.logger.info(f"License VALID for {ip} | expire_at={expire_at}")
        return jsonify({"valid": True, "expire_at": expire_at})

    app.logger.warning(f"Invalid token from {ip}")
    return jsonify({"valid": False, "reason": "invalid_token"})

@app.route("/health", methods=["GET"])
def health():
    token_set = os.path.exists(TOKEN_FILE) and get_token() != ""
    return jsonify({
        "status": "ok",
        "token_configured": token_set,
        "package": get_package(),
        "cache_ttl_seconds": CACHE_TTL
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
