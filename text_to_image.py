import boto3
import json
import base64
import os
from typing import Optional, Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class TitanImageGenerator:
    DEFAULT_NEGATIVE_PROMPT = (
        "blurry, bad quality, distorted"  # Default negative prompt
    )

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
        profile_name: Optional[str] = None,
    ):
        """
        Initialize Bedrock client for Titan Image Generator model.
        """
        try:
            # Initialize session
            if profile_name:
                session = boto3.Session(profile_name=profile_name)
            elif aws_access_key_id and aws_secret_access_key:
                session = boto3.Session(
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key,
                    region_name=region_name,
                )
            else:
                # Try to use environment variables
                aws_access_key = os.getenv("AWS_ACCESS_KEY")
                aws_secret_key = os.getenv("AWS_SECRET_KEY")

                if aws_access_key and aws_secret_key:
                    print("Using credentials from .env file")
                    session = boto3.Session(
                        aws_access_key_id=aws_access_key,
                        aws_secret_access_key=aws_secret_key,
                        region_name=region_name,
                    )
                else:
                    raise Exception("No AWS credentials found in .env file")

            # Create Bedrock runtime client
            self.bedrock = session.client(
                service_name="bedrock-runtime", region_name=region_name
            )
            print("Successfully initialized Bedrock client")

        except Exception as e:
            raise Exception(f"Failed to initialize AWS session: {str(e)}")

    def validate_parameters(
        self, width: int, height: int, num_images: int, cfg_scale: int
    ) -> bool:
        """
        Validate input parameters.
        """
        if width % 64 != 0 or height % 64 != 0:
            raise ValueError("Width and height must be multiples of 64")
        if num_images < 1 or num_images > 10:
            raise ValueError("Number of images must be between 1 and 10")
        if cfg_scale < 1 or cfg_scale > 35:
            raise ValueError("CFG scale must be between 1 and 35")
        return True

    def generate_images(
        self,
        prompt: str,
        cfg_scale: int = 8,
        seed: int = 42,
        quality: str = "standard",
        width: int = 1024,
        height: int = 1024,
        num_images: int = 3,
        output_dir: str = "generated_images",
        negative_prompt: Optional[str] = None,
    ) -> List[str]:
        """
        Generate images using Titan Image Generator model.
        """
        try:
            # Validate parameters
            self.validate_parameters(width, height, num_images, cfg_scale)

            # Use default negative prompt if none provided
            if not negative_prompt:
                negative_prompt = self.DEFAULT_NEGATIVE_PROMPT

            # Prepare the request body
            request_body = {
                "textToImageParams": {"text": prompt, "negativeText": negative_prompt},
                "taskType": "TEXT_IMAGE",
                "imageGenerationConfig": {
                    "cfgScale": cfg_scale,
                    "seed": seed,
                    "quality": quality,
                    "width": width,
                    "height": height,
                    "numberOfImages": num_images,
                },
            }

            print(f"Request body: {json.dumps(request_body, indent=2)}")  # Debug print

            # Create output directory if it doesn't exist
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            print(f"Generating {num_images} images with prompt: '{prompt}'")

            # Invoke the model
            response = self.bedrock.invoke_model(
                modelId="amazon.titan-image-generator-v1",
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response.get("body").read())

            # Save images and collect paths
            image_paths = []
            for idx, image_data in enumerate(response_body.get("images", [])):
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)

                # Generate filename
                filename = f"{output_dir}/image_{seed}_{idx + 1}.png"

                # Save image
                with open(filename, "wb") as f:
                    f.write(image_bytes)
                print(f"Saved image {idx + 1} to {filename}")

                image_paths.append(filename)

            return image_paths

        except Exception as e:
            raise Exception(f"Error generating images: {str(e)}")


def test_image_generator():
    """Test function for the TitanImageGenerator class"""
    try:
        print("Testing AWS credentials from .env file...")
        aws_access_key = os.getenv("AWS_ACCESS_KEY")
        aws_secret_key = os.getenv("AWS_SECRET_KEY")

        if not aws_access_key or not aws_secret_key:
            raise Exception("AWS credentials not found in .env file")

        print(f"Found AWS access key: {aws_access_key[:5]}...")

        # Initialize generator
        generator = TitanImageGenerator(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name="us-east-1",
        )

        # Test image generation
        prompt = "show me the Earth from space, highly detailed, realistic"
        print(f"\nTesting image generation with prompt: '{prompt}'")

        image_paths = generator.generate_images(
            prompt=prompt,
            cfg_scale=10,
            seed=123,
            quality="standard",
            width=1024,
            height=1024,
            num_images=1,
            output_dir="test_generated_images",
            negative_prompt="blurry, low quality, distorted, bad anatomy, pixelated",
        )

        print("\nTest Results:")
        print(f"Successfully generated {len(image_paths)} images")
        for path in image_paths:
            print(f"Image saved at: {path}")

        return True

    except Exception as e:
        print(f"\nTest failed with error: {str(e)}")
        return False


if __name__ == "__main__":
    test_image_generator()