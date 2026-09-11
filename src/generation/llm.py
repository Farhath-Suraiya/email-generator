import os
import time
import re
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        
        default_model = "gemini-3.6-flash" if self.provider in ["gemini", "google"] else "gpt-4o-mini"
        self.model_name = model_name or os.getenv("LLM_MODEL", default_model)

    def generate(self, system_instruction: str, user_prompt: str, max_retries: int = 5) -> str:
        if not self.api_key or not self.api_key.strip():
            raise ValueError("LLM API key is missing. Please set LLM_API_KEY in environment or .env file.")

        for attempt in range(max_retries):
            try:
                if self.provider == "openai":
                    import openai
                    client = openai.OpenAI(api_key=self.api_key)
                    response = client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": system_instruction},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.3
                    )
                    text = response.choices[0].message.content

                elif self.provider in ["gemini", "google"]:
                    from google import genai
                    from google.genai import types
                    client = genai.Client(api_key=self.api_key)
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.3
                    )
                    response = client.models.generate_content(
                        model=self.model_name,
                        contents=user_prompt,
                        config=config
                    )
                    text = response.text
                else:
                    raise ValueError(f"Unsupported LLM provider: '{self.provider}'")

                if text and text.strip():
                    return text.strip()

            except Exception as e:
                err_str = str(e)
                # Check for 429 Rate Limit / Quota Exceeded
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Rate limit" in err_str:
                    if attempt < max_retries - 1:
                        # Extract suggested retry delay if present, else wait 12s
                        match = re.search(r'retry in (\d+(?:\.\d+)?)s', err_str, re.IGNORECASE)
                        wait_time = float(match.group(1)) + 2.0 if match else 12.0
                        print(f"Rate limit hit (429). Retrying in {wait_time:.1f}s... (Attempt {attempt+1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                
                if isinstance(e, ValueError):
                    raise e
                raise RuntimeError(f"LLM API call failed: {err_str}") from e

        raise ValueError("LLM returned an empty or invalid response.")
