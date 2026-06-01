import json
import logging
import requests
from config import Config

logger = logging.getLogger(__name__)

class GroqClient:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def analyze_article(self, title: str, description: str, content: str, source: str):
        if not self.api_key:
            return {
                "summary": description or content[:250],
                "category": "General Knowledge",
                "credibility_score": 80,
                "suspicious_reason": "",
                "headline": title,
            }

        article_text = f"Title: {title}\nSource: {source}\n\nSummary or description:\n{description}\n\nFull content:\n{content}"
        prompt = (
            "Analyze the article below and return only valid JSON. "
            "Output keys: summary, category, credibility_score, suspicious_reason, headline. "
            "Use 3-4 lines for the summary. "
            "Category must be one of: Latest News, Sports, International Relations, General Knowledge, Science & Technology, Indian Polity, Finance & Economy, Business, Entertainment. "
            "Set credibility_score from 0 to 100. "
            "If the article looks suspicious, add a short suspicious_reason; otherwise return an empty string.\n\n"
            f"Article:\n{article_text}\n"
        )

        payload = {
            "input": prompt,
            "max_output_tokens": 250,
            "temperature": 0.2,
        }
        url = f"{self.base_url}/{self.model}/outputs"

        try:
            response = requests.post(url, headers=self.headers, json=payload, timeout=20)
            response.raise_for_status()
            data = response.json()
            raw_output = self._extract_text_output(data)
            parsed = self._parse_json(raw_output)

            if parsed:
                return {
                    "summary": parsed.get("summary", description or content[:250]),
                    "category": parsed.get("category", "General Knowledge"),
                    "credibility_score": float(parsed.get("credibility_score", 70)),
                    "suspicious_reason": parsed.get("suspicious_reason", ""),
                    "headline": parsed.get("headline", title),
                }
        except Exception as ex:
            logger.warning(f"Groq analysis failed: {ex}")

        return {
            "summary": description or content[:250],
            "category": "General Knowledge",
            "credibility_score": 70,
            "suspicious_reason": "",
            "headline": title,
        }

    def _extract_text_output(self, response_json):
        if isinstance(response_json, dict):
            if "output" in response_json:
                output = response_json["output"]
                if isinstance(output, list) and output:
                    first = output[0]
                    if isinstance(first, dict) and "content" in first:
                        return first["content"]
                    return str(first)
            if "text" in response_json:
                return response_json["text"]
        return json.dumps(response_json)

    def _parse_json(self, text_value: str):
        text_value = text_value.strip()
        try:
            return json.loads(text_value)
        except json.JSONDecodeError:
            # Try to locate JSON object inside the returned text.
            start = text_value.find("{")
            end = text_value.rfind("}")
            if start != -1 and end != -1:
                try:
                    return json.loads(text_value[start : end + 1])
                except json.JSONDecodeError:
                    return None
        return None
