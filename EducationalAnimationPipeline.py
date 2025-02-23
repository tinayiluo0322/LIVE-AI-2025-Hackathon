import os
from typing import List, Dict, Tuple
from pathlib import Path
import asyncio
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor

# Import from your modules
from entity_extraction import EntityExtractor
from entity_enrichment_prompt import PromptEnricher
from text_to_image import TitanImageGenerator
from image_to_animation import AnimationGenerator

# Load environment variables
load_dotenv()


class EducationalAnimationPipeline:
    def __init__(
        self, output_base_dir: str = "pipeline_outputs", max_parallel_tasks: int = 3
    ):
        """
        Initialize the pipeline with all necessary components.
        """
        self.output_base_dir = output_base_dir
        self.max_parallel_tasks = max_parallel_tasks

        # Create output directories
        self.image_dir = os.path.join(output_base_dir, "generated_images")
        self.animation_dir = os.path.join(output_base_dir, "animations")
        os.makedirs(self.image_dir, exist_ok=True)
        os.makedirs(self.animation_dir, exist_ok=True)

        # Initialize components
        self.entity_extractor = EntityExtractor()
        self.prompt_enricher = PromptEnricher()
        self.image_generator = TitanImageGenerator(
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
        )
        self.animation_generator = AnimationGenerator(output_dir=self.animation_dir)

    async def process_entity(self, entity: str, seed: int = 42) -> Dict:
        """Process a single entity through the pipeline."""
        try:
            # 1. Enrich the prompt
            enriched_prompt = self.prompt_enricher.enrich_prompt(entity)
            print(f"\nProcessing entity: {entity}")
            print(f"Enriched prompt: {enriched_prompt}")

            # 2. Generate image
            image_paths = self.image_generator.generate_images(
                prompt=enriched_prompt,
                seed=seed,
                num_images=1,
                output_dir=self.image_dir,
            )

            if not image_paths:
                raise Exception(f"Image generation failed for {entity}")

            image_path = image_paths[0]
            print(f"Generated image: {image_path}")

            # 3. Generate animation
            animation_path, success = self.animation_generator.generate_animation(
                image_path=image_path,
                prompt=enriched_prompt,
                seed=seed,
                output_filename=f"animation_{entity}_{seed}.gif",
            )

            if not success:
                raise Exception(f"Animation generation failed for {entity}")

            print(f"Generated animation: {animation_path}")

            return {
                "entity": entity,
                "prompt": enriched_prompt,
                "image_path": image_path,
                "animation_path": animation_path,
            }

        except Exception as e:
            print(f"Error processing entity {entity}: {str(e)}")
            return {"entity": entity, "error": str(e)}

    async def run_pipeline(self, educational_content: str) -> List[Dict]:
        """
        Run the complete pipeline.

        Args:
            educational_content: The educational text content

        Returns:
            List of dictionaries containing results for each entity
        """
        try:
            print("Starting pipeline...")

            # 1. Extract entities
            print("\nExtracting entities...")
            entities = self.entity_extractor.extract_concepts(educational_content)
            print(f"Extracted entities: {entities}")

            if "error" in entities[0]:
                raise Exception("Entity extraction failed")

            # 2. Process each entity in parallel
            print("\nProcessing entities in parallel...")
            tasks = []
            for i, entity in enumerate(entities):
                tasks.append(self.process_entity(entity, seed=42 + i))

            results = await asyncio.gather(*tasks)
            return results

        except Exception as e:
            print(f"Pipeline error: {str(e)}")
            return []


def test_pipeline():
    """Test the complete pipeline"""
    # Test educational content
    test_content = """
    "The Sun is our closest star, a massive ball of plasma that powers our solar system. 
    Through nuclear fusion in its core, it generates immense energy that radiates outward. 
    This energy travels through space as electromagnetic radiation, including visible light, 
    which takes about 8 minutes to reach Earth. Earth orbits around the Sun while rotating 
    on its tilted axis, causing our days and seasons."
    """

    # Initialize pipeline
    pipeline = EducationalAnimationPipeline()

    # Run pipeline
    print("Testing educational animation pipeline...")
    print("\nInput content:", test_content)

    # Run async pipeline
    results = asyncio.run(pipeline.run_pipeline(test_content))

    # Print results
    print("\nPipeline Results:")
    for result in results:
        if "error" in result:
            print(f"\nError processing {result['entity']}: {result['error']}")
        else:
            print(f"\nEntity: {result['entity']}")
            print(f"Prompt: {result['prompt']}")
            print(f"Image: {result['image_path']}")
            print(f"Animation: {result['animation_path']}")


if __name__ == "__main__":
    test_pipeline()