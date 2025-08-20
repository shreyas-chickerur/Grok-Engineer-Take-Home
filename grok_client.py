from typing import Dict, List, Any
import os, json, random
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class GrokClient:
    def __init__(self, api_key: str | None = None, api_url: str | None = None, model: str | None = None):
        self.api_key = api_key or os.getenv("GROK_API_KEY")
        self.api_url = api_url or os.getenv("GROK_API_URL")
        self.model = model or os.getenv("GROK_MODEL")
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_url
        )
        
    @property
    def dry_run(self) -> bool:
        return not bool(self.api_key)
    
    def chat(self, system: str, user: str) -> Dict[str, Any]:
        if self.dry_run:
            fake = {
                "choices": [{
                    "message": {
                        "content": json.dumps({
                            "score": random.randint(55, 92),
                            "rationale": "Dry-run rationale based on provided fields.",
                            "tags": ["ai", "saas", "mid-market"]
                        })
                    }
                }]
            }
            return fake
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            temperature= 0.2
        )
        return response
        
        
    def parse_json_content(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # Extract the first message content and parse as JSON.
        try:
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception:
            return {"error": "Failed to parse Grok response", "raw": response}
