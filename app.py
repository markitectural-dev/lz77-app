from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def lz77_encode(text, window_size=32, lookahead_size=16):
    """
    Кодирование строки алгоритмом LZ77.
    Возвращает список троек (d, k, c) и пошаговую трассировку.
    """
    encoded = []
    steps = []
    i = 0

    while i < len(text):
        best_d = 0
        best_k = 0

        search_start = max(0, i - window_size)

        for d in range(1, min(i, window_size) + 1):
            start = i - d
            k = 0
            while i + k < len(text) - 1 and k < lookahead_size:
                if text[start + (k % d)] == text[i + k]:
                    k += 1
                else:
                    break
            if k > best_k:
                best_k = k
                best_d = d

        if best_k > 0 and i + best_k < len(text):
            next_char = text[i + best_k]
            triple = (best_d, best_k, next_char)
        else:
            best_d = 0
            best_k = 0
            next_char = text[i]
            triple = (0, 0, next_char)

        search_buf = text[search_start:i] if i > 0 else "(пусто)"
        lookahead_buf = text[i:min(i + lookahead_size + 1, len(text))]

        steps.append({
            "step": len(steps) + 1,
            "position": i,
            "search_buffer": search_buf,
            "lookahead_buffer": lookahead_buf,
            "match": f"d={best_d}, k={best_k}" if best_k > 0 else "нет",
            "triple": f"({triple[0]}, {triple[1]}, '{triple[2]}')",
            "d": triple[0],
            "k": triple[1],
            "c": triple[2],
        })

        encoded.append(triple)
        i += best_k + 1

    return encoded, steps


def lz77_decode(triples):
    """
    Декодирование последовательности троек LZ77.
    Возвращает восстановленную строку и пошаговую трассировку.
    """
    result = []
    steps = []

    for idx, (d, k, c) in enumerate(triples):
        copied = ""
        if k > 0:
            start = len(result) - d
            for j in range(k):
                char = result[start + (j % d)]
                result.append(char)
                copied += char
        result.append(c)

        steps.append({
            "step": idx + 1,
            "triple": f"({d}, {k}, '{c}')",
            "copied": copied if copied else "—",
            "added_char": c,
            "result_so_far": "".join(result),
        })

    return "".join(result), steps


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/encode", methods=["POST"])
def encode():
    data = request.get_json()
    text = data.get("text", "")
    window_size = int(data.get("window_size", 32))
    lookahead_size = int(data.get("lookahead_size", 16))

    if not text:
        return jsonify({"error": "Пустая строка"}), 400

    if len(text) > 1000:
        return jsonify({"error": "Строка слишком длинная (макс. 1000 символов)"}), 400

    encoded, steps = lz77_encode(text, window_size, lookahead_size)
    triples_str = [f"({d}, {k}, '{c}')" for d, k, c in encoded]

    return jsonify({
        "original": text,
        "original_length": len(text),
        "encoded_count": len(encoded),
        "triples": triples_str,
        "steps": steps,
    })


@app.route("/decode", methods=["POST"])
def decode():
    data = request.get_json()
    triples_raw = data.get("triples", [])

    triples = []
    for t in triples_raw:
        triples.append((int(t["d"]), int(t["k"]), t["c"]))

    decoded, steps = lz77_decode(triples)

    return jsonify({
        "decoded": decoded,
        "steps": steps,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
