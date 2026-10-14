from groq import Groq
import config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY set nahi hai (.env check karo)")
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def ask(system, user, temperature=0.2, max_tokens=900):
    args = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # gpt-oss reasoning model hai, wo soch-vichar mein bhi tokens kharch karta hai.
    # isliye jagah zyada dete hain aur effort low rakhte hain
    if "gpt-oss" in config.GROQ_MODEL:
        args["max_tokens"] = max(max_tokens, 800)
        args["reasoning_effort"] = "low"

    client = _get_client()
    try:
        resp = client.chat.completions.create(**args)
    except TypeError:
        # purani groq library reasoning_effort nahi jaanti
        args.pop("reasoning_effort", None)
        resp = client.chat.completions.create(**args)

    return (resp.choices[0].message.content or "").strip()
