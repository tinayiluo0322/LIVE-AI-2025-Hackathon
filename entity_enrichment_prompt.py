from typing import Dict, List
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PromptEnricher:
    def __init__(self, api_key: str = None):
        """Initialize the PromptEnricher."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")

        self.client = OpenAI(api_key=self.api_key)

        # Default prompt enrichment templates
        self.default_templates = {
            "Earth": "show me the Earth from space, highly detailed, realistic",
            "Sun": "show me the Sun with solar flares and corona, highly detailed, scientifically accurate",
            "Moon": "show me the Moon's surface with craters and details, photorealistic view from space",
            "galaxy": "show me a spiral galaxy with stars and cosmic dust, scientifically accurate",
            "blackhole": "show me a black hole with accretion disk and gravitational lensing, scientifically accurate",
        }

    def enrich_prompt(self, entity: str) -> str:
        """
        Convert a simple entity into a detailed image generation prompt.
        First checks predefined templates, then uses GPT for custom enrichment.

        Args:
            entity: Single word entity to enrich

        Returns:
            Enriched prompt string
        """
        try:
            # Check if we have a predefined template
            if entity in self.default_templates:
                return self.default_templates[entity]

            # If no template exists, use GPT to create a detailed prompt
            system_prompt = """
            You are an expert at creating detailed, descriptive prompts for image generation.
            Convert simple entities into detailed prompts that will generate high-quality, educational images.
            
            Rules:
            1. Always include "show me" at the start
            2. Add relevant scientific or educational details
            3. Include "highly detailed, realistic" at the end
            4. Keep the prompt clear and focused
            5. Return ONLY the prompt text, no explanations or additional text
            
            Example input: "Earth"
            Example output: show me the Earth from space, highly detailed, realistic
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Create a detailed prompt for: {entity}",
                    },
                ],
                temperature=0.7,
            )

            enriched_prompt = response.choices[0].message.content.strip()
            return enriched_prompt

        except Exception as e:
            print(f"Error enriching prompt: {str(e)}")
            # Fallback to a safe default format
            return f"show me {entity}, highly detailed, realistic"

    def enrich_prompts(self, entities: List[str]) -> Dict[str, str]:
        """
        Convert multiple entities into detailed prompts.

        Args:
            entities: List of entities to enrich

        Returns:
            Dictionary mapping original entities to enriched prompts
        """
        enriched = {}
        for entity in entities:
            enriched[entity] = self.enrich_prompt(entity)
        return enriched


def test_prompt_enricher():
    """Test the PromptEnricher"""
    try:
        # Initialize enricher
        enricher = PromptEnricher()

        # Test cases
        test_entities = [
            "Earth",  # Should use template
            "Mars",  # Should use GPT
            "galaxy",  # Should use template
            "nebula",  # Should use GPT
        ]

        print("Testing prompt enrichment...")

        # Test individual enrichment
        print("\nTesting individual enrichment:")
        for entity in test_entities:
            enriched = enricher.enrich_prompt(entity)
            print(f"\nEntity: {entity}")
            print(f"Enriched: {enriched}")

        # Test batch enrichment
        print("\nTesting batch enrichment:")
        enriched_dict = enricher.enrich_prompts(test_entities)
        for entity, prompt in enriched_dict.items():
            print(f"\nEntity: {entity}")
            print(f"Enriched: {prompt}")

    except Exception as e:
        print(f"Test failed with error: {str(e)}")


if __name__ == "__main__":
    test_prompt_enricher()
