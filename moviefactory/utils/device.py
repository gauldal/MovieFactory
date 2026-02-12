from flask import request

def is_mobile_request() -> bool:
    ua = request.headers.get("User-Agent", "").lower()

    mobile_keywords = [
        "iphone",
        "android",
        "ipad",
        "ipod",
        "mobile"
    ]

    return any(k in ua for k in mobile_keywords)
