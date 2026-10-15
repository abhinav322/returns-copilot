import httpx


OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:4b-instruct"


def clean_model_response(content: str) -> str:

    if "</think>" in content:
        content = content.split(
            "</think>",
            1
        )[1]

    return content.strip()


def generate_response(prompt: str) -> str:

    payload = {
        "model": MODEL_NAME,

        "keep_alive": "10m",

        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a helpful customer support assistant. "
                    "Answer clearly and concisely. "
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        "stream": False,


        "options": {
            "temperature": 0.2,
            "num_predict": 180
        },
    }

    response = httpx.post(
        OLLAMA_URL,
        json=payload,
        timeout=300.0,
    )

    response.raise_for_status()

    data = response.json()

    content = data[
        "message"
    ][
        "content"
    ]

    return clean_model_response(
        content
    )