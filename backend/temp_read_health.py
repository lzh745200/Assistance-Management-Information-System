with open("health_result.txt", "rb") as f:
    raw = f.read()
for enc in ["utf-16-le", "utf-16", "gbk", "utf-8-sig", "utf-8", "latin-1"]:
    try:
        text = raw.decode(enc)
        print(text)
        break
    except Exception:
        continue
