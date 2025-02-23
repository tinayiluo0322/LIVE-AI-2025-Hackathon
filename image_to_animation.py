import os
import requests
import base64
from pathlib import Path
from typing import Optional, Union, Tuple
from PIL import Image

class AnimationGenerator:
    def __init__(self, colab_url: str, output_dir: str = "outputs"):
        """
        Initialize the AnimationGenerator with Colab backend.
        
        Args:
            colab_url (str): Ngrok URL from Colab notebook
            output_dir (str): Directory to save animations
        """
        self.colab_url = colab_url + "/generate"
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_animation(
        self,
        image_path: Union[str, Path],
        prompt: str,
        negative_prompt: Optional[str] = None,
        seed: int = 0,
        num_frames: int = 16,
        output_filename: Optional[str] = None,
    ) -> Tuple[str, bool]:
        try:
            # Read and encode image
            with open(image_path, 'rb') as img_file:
                img_data = base64.b64encode(img_file.read()).decode('utf-8')
            
            # Prepare payload
            payload = {
                'image': img_data,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'seed': seed,
                'num_frames': num_frames
            }
            
            # Send request to Colab
            print("Sending request to Colab...")
            # Add timeout and verify parameters
            response = requests.post(
                self.colab_url, 
                json=payload, 
                timeout=30,  # 30 seconds timeout
                verify=True
            )
            response.raise_for_status()
            
            # Save received animation
            if output_filename is None:
                output_filename = f"animation_{seed}.gif"
            output_path = os.path.join(self.output_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(response.json()['animation']))
            
            print(f"Animation saved as {output_path}")
            return output_path, True
        
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")
            print("Please check:")
            print("1. Is your Colab notebook running?")
            print("2. Did you copy the correct ngrok URL?")
            print("3. Is your ngrok authentication token valid?")
            return "", False
        
        except Exception as e:
            print(f"Error during animation generation: {str(e)}")
            return "", False

# Update test function
def test_animation_generator(colab_url: str):
    """Test function for the AnimationGenerator class."""
    # Test connection first
    try:
        # Test base URL without /generate endpoint
        base_url = colab_url.rstrip('/generate')
        print(f"Testing connection to {base_url}...")
        response = requests.get(base_url, timeout=10)
        response.raise_for_status()
        print("Successfully connected to Colab server")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to Colab server: {e}")
        print("\nPlease check:")
        print("1. Is your Colab notebook running?")
        print("2. Did you copy the complete ngrok URL?")
        print("3. Is the URL formatted as 'https://something.ngrok.io'?")
        return
    
    """Test function for the AnimationGenerator class."""
    os.makedirs("pipeline_outputs/generated_images", exist_ok=True)
    os.makedirs("pipeline_outputs/animations", exist_ok=True)
    
    test_image_path = "./pipeline_outputs/generated_images/test_image.png"
    
    # Create a test image if it doesn't exist
    if not os.path.exists(test_image_path):
        img = Image.new('RGB', (512, 512), color='white')
        img.save(test_image_path)

    test_prompt = "a shining sun"
    generator = AnimationGenerator(colab_url=colab_url, 
                                 output_dir="./pipeline_outputs/animations")
    
    output_path, success = generator.generate_animation(
        image_path=test_image_path,
        prompt=test_prompt,
        seed=42,
        num_frames=8
    )

    if success:
        print(f"Test successful! Animation saved to: {output_path}")
    else:
        print("Test failed!")

if __name__ == "__main__":
    # Replace with the Ngrok URL from your Colab notebook
    COLAB_URL = input("Enter the Colab server URL: ")
    test_animation_generator(COLAB_URL)