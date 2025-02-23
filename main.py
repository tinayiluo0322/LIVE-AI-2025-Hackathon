from InterestExplorer import InterestExplorer
import os
from ProcessInterest import process_interest
from EducationalAnimationPipeline import EducationalAnimationPipeline
import asyncio
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()

    # Get API key from environment
    API_KEY = os.getenv("OPENAI_API_KEY")
    if not API_KEY:
        raise Exception("No OpenAI API key found in .env file")
    
    # Initialize the explorer
    explorer = InterestExplorer(API_KEY)
    
    try:
        # Process interest and get results
        user_interest = process_interest(explorer)
        test_content = user_interest['focused_exploration']

        # Initialize the pipeline
        pipeline = EducationalAnimationPipeline()

        # Run pipeline
        print("Testing educational animation pipeline...")
        print("\nInput content:", test_content)

        # Run async pipeline
        results = asyncio.run(pipeline.run_pipeline(test_content))
        return results

    except Exception as e:
        print(f"Error in main: {str(e)}")
        return None

if __name__ == "__main__":
    results = main()
    if results:
        print("\nPipeline Results:")
        for result in results:
            if "error" in result:
                print(f"\nError processing {result.get('entity', 'unknown')}: {result['error']}")
            else:
                print(f"\nEntity: {result['entity']}")
                print(f"Prompt: {result['prompt']}")
                print(f"Image: {result['image_path']}")
                print(f"Animation: {result['animation_path']}")

