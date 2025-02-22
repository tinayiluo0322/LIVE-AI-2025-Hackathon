import os
from typing import List, Tuple
from openai import OpenAI
import ast
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EntityExtractor:
    def __init__(self, api_key: str = None):
        """Initialize the EntityExtractor."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not found")

        self.client = OpenAI(api_key=self.api_key)

    def extract_concepts(self, text: str) -> List[str]:
        """
        Extract key educational concepts from text that could be visualized.

        Args:
            text: Educational content to extract concepts from

        Returns:
            List of key concepts that can be visualized
        """
        system_prompt = """
        You are an expert at identifying key educational concepts that can be visualized.
        From the given educational content, extract main concepts that would make good visuals or animations.
        
        Rules:
        1. Only extract single-word concepts that can be clearly visualized
        2. Focus on physical objects and clear visual concepts (e.g., "Earth", "Sun", "galaxy")
        3. Return ONLY a Python list of strings ["word1", "word2", ...]
        4. Each concept must be a single word, no phrases or compound words
        5. Limit to the most important 3-5 concepts
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Extract key visualizable concepts from:\n{text}",
                    },
                ],
                temperature=0.1,
            )

            output = response.choices[0].message.content.strip()

            try:
                concepts = ast.literal_eval(output)
                if isinstance(concepts, list) and all(
                    isinstance(item, str) for item in concepts
                ):
                    return concepts
                else:
                    print("Invalid format returned. Using error handling.")
                    return ["error in concept extraction"]

            except (ValueError, SyntaxError) as e:
                print(f"Error parsing response: {e}")
                return ["error in concept extraction"]

        except Exception as e:
            print(f"API Error: {e}")
            return ["error in concept extraction"]


def test_entity_extractor():
    """Test the EntityExtractor"""
    try:
        # Initialize extractor
        extractor = EntityExtractor()

        # Test text
        test_text = """
        The Sun is our closest star, a massive ball of plasma that powers our solar system. Through nuclear fusion in its core, it generates immense energy that radiates outward. This energy travels through space as electromagnetic radiation, including visible light, which takes about 8 minutes to reach Earth. Earth orbits around the Sun while rotating on its tilted axis, causing our days and seasons. Accompanying Earth is the Moon, its only natural satellite, which orbits approximately every 27 days. The Moon's gravitational pull influences Earth's tides, and its phases result from the changing angles of sunlight reflecting off its surface as it moves around our planet.
        """

        print("Testing with educational content about the Sun...")
        print("\nInput text:", test_text)

        concepts = extractor.extract_concepts(test_text)

        print("\nExtracted concepts:", concepts)

    except Exception as e:
        print(f"Test failed with error: {str(e)}")


if __name__ == "__main__":
    test_entity_extractor()
