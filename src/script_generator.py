"""Fact-grounded caption generation with a dependable local fallback."""

import json
import os
import re


def template_captions(property_name, location, price, property_type, features, contact, count):
    facts = [str(item).strip() for item in features if str(item).strip()]
    candidates = [f"Meet {property_name}", f"{property_type} · {location}"]
    candidates.extend(facts)
    if price:
        candidates.append(f"Offered at {price}")
    candidates.extend([f"A closer look at {property_name}", contact or "Get in touch to learn more"])
    captions = []
    for caption in candidates:
        if caption not in captions:
            captions.append(caption)
        if len(captions) == count:
            break
    while len(captions) < count:
        captions.insert(max(1, len(captions) - 1), f"Explore {property_name}")
    return captions[:count]


def generate_captions(property_name, location, price, property_type, features, contact, count, *, api_key=None, model=None):
    fallback = template_captions(property_name, location, price, property_type, features, contact, count)
    key = (api_key if api_key is not None else os.getenv("GROQ_API_KEY", "")).strip()
    model = (model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")).strip()
    if not key:
        return fallback, "Built-in templates"
    try:
        from groq import Groq

        facts = {"name": property_name, "location": location, "price": price, "type": property_type, "features": features, "contact": contact}
        response = Groq(api_key=key, timeout=20, max_retries=1).chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Write short, polished real-estate video captions. Use only facts in the JSON. Do not infer visual details, amenities, distances, legal status, returns, or other claims. Return a JSON object with a captions array of strings."},
                {"role": "user", "content": f"Write exactly {count} distinct captions using these facts: {json.dumps(facts, ensure_ascii=False)}"},
            ],
            temperature=0.4,
            max_tokens=500,
            response_format={"type": "json_object"},
        )
        text = response.choices[0].message.content.strip()
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            parsed = parsed.get("captions")
        if not isinstance(parsed, list) or len(parsed) != count or not all(isinstance(item, str) and item.strip() for item in parsed):
            return fallback, "Built-in templates (AI response was invalid)"
        # Reject a caption containing a new number, reducing unsupported numeric claims.
        supplied_numbers = set(re.findall(r"\d+(?:[.,]\d+)*", json.dumps(facts)))
        for item in parsed:
            if set(re.findall(r"\d+(?:[.,]\d+)*", item)) - supplied_numbers:
                return fallback, "Built-in templates (AI response contained an unsupported number)"
        return [item.strip() for item in parsed], f"Groq · {model}"
    except Exception:
        return fallback, "Built-in templates (AI unavailable)"
