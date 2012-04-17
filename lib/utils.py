import urllib

def urlencode(query, doseq=0):
    if hasattr(query, "items"):
        query = query.items()

    cleaned = []

    for el in query:
        key = el[0].encode('utf-8')
        val = el[1]

        if isinstance(val, list):
            cleaned_val = []

            for val_el in val:
                cleaned_val.append(val_el.encode('utf-8'))

            val = cleaned_val
        else:
            try:
                val = val.encode('utf-8')
            except:
                pass

        cleaned.append((key, val))

    return urllib.urlencode(cleaned, doseq)
