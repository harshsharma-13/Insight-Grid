"""
AI Consumer Intelligence Platform

Module 13A
Ollama Provider

Runs local LLM inference using Ollama.
"""

import json
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"


class OllamaProvider:

    def __init__(self, model="llama3.2:3b"):
        self.model = model

    def generate_json(self, prompt: str):

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }

        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        result = response.json()

        text = result["response"]

        try:
            return json.loads(text)

        except json.JSONDecodeError:

            return {
                "executive_summary": text,
                "strengths": [],
                "pain_points": [],
                "platform_insight": "",
                "recommendation": "",
                "error": "Model returned non-JSON output"
            }


def test():

    provider = OllamaProvider()

    prompt = """
Return ONLY valid JSON.

Analyze this smartphone.

Positive sentiment: 82%

Strengths:
Battery
Display
Performance

Weaknesses:
Heating
Camera

Platform:
Flipkart users are slightly happier.

Return JSON with keys:

executive_summary
strengths
pain_points
platform_insight
recommendation
"""

    result = provider.generate_json(prompt)

    print(json.dumps(result, indent=4))


if __name__ == "__main__":
    test()