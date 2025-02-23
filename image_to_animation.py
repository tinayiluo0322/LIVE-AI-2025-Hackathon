import os
import torch
from diffusers import EulerDiscreteScheduler, MotionAdapter, PIAPipeline
from diffusers.utils import export_to_gif, load_image
import matplotlib.pyplot as plt
import gc
from typing import Optional, Union, Tuple
from pathlib import Path


class AnimationGenerator:
    def __init__(self, output_dir: str = "outputs"):
        """
        Initialize the AnimationGenerator.

        Args:
            output_dir (str): Directory to save output animations
        """
        self.output_dir = output_dir
        self.pipe = None
        self.adapter = None
        self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        print(f"Using device: {self.device}")
        os.makedirs(output_dir, exist_ok=True)

    def _setup_pipeline(self):
        """Set up the PIA pipeline and motion adapter."""
        try:
            print("Loading motion adapter...")
            self.adapter = MotionAdapter.from_pretrained(
                "openmmlab/PIA-condition-adapter"
            )

            print("Loading PIA pipeline...")
            self.pipe = PIAPipeline.from_pretrained(
                "SG161222/Realistic_Vision_V6.0_B1_noVAE",
                motion_adapter=self.adapter,
                torch_dtype=torch.float16,
            )

            # Move pipeline to appropriate device
            self.pipe.to(self.device)

            # Set up scheduler and optimizations
            self.pipe.scheduler = EulerDiscreteScheduler.from_config(
                self.pipe.scheduler.config
            )
            # Only enable these optimizations for CUDA
            if self.device == "cuda":
                self.pipe.enable_model_cpu_offload()
                self.pipe.enable_vae_slicing()

            # self.pipe.enable_model_cpu_offload()
            # self.pipe.enable_vae_slicing()

        except Exception as e:
            raise RuntimeError(f"Failed to setup pipeline: {str(e)}")

    def _cleanup(self):
        """Clean up GPU memory."""
        if hasattr(self, "pipe"):
            del self.pipe
        if hasattr(self, "adapter"):
            del self.adapter
        torch.cuda.empty_cache()
        gc.collect()

    def generate_animation(
        self,
        image_path: Union[str, Path],
        prompt: str,
        negative_prompt: Optional[str] = None,
        seed: int = 0,
        num_frames: int = 16,
        output_filename: Optional[str] = None,
    ) -> Tuple[str, bool]:
        """
        Generate an animation from an input image.

        Args:
            image_path: Path to input image
            prompt: Text prompt for animation
            negative_prompt: Negative prompt for generation
            seed: Random seed for reproducibility
            num_frames: Number of frames to generate
            output_filename: Custom filename for output GIF

        Returns:
            Tuple[str, bool]: (Path to output GIF, Success status)
        """
        try:
            # Setup pipeline if not already set up
            if self.pipe is None:
                self._setup_pipeline()

            # Clear CUDA cache
            torch.cuda.empty_cache()
            gc.collect()

            # Load and preprocess image
            print("Loading input image...")
            image = load_image(image_path)
            image = image.resize((512, 512))

            # Set default negative prompt if none provided
            if negative_prompt is None:
                negative_prompt = (
                    "wrong white balance, dark, sketches, worst quality, low quality"
                )

            # Set up generator
            generator = torch.Generator("cpu").manual_seed(seed)

            # Generate animation
            print("Generating animation...")
            output = self.pipe(
                image=image,
                prompt=prompt,
                negative_prompt=negative_prompt,
                generator=generator,
                num_frames=num_frames,
            )

            # Prepare output path
            if output_filename is None:
                output_filename = f"animation_{seed}.gif"
            output_path = os.path.join(self.output_dir, output_filename)

            # Save the animation
            frames = output.frames[0]
            export_to_gif(frames, output_path)
            print(f"Animation saved as {output_path}")

            return output_path, True

        except Exception as e:
            print(f"Error during animation generation: {str(e)}")
            return "", False

        finally:
            self._cleanup()


def test_animation_generator():
    """Test function for the AnimationGenerator class."""
   # Create test directories
    os.makedirs("pipeline_outputs/generated_images", exist_ok=True)
    os.makedirs("pipeline_outputs/animations", exist_ok=True)
    # Create a test image if it doesn't exist
    test_image_path = "./pipeline_outputs/generated_images/image_42_1.png"


    test_prompt = "an shinning Sun"

    # Create generator instance
    generator = AnimationGenerator(output_dir="./pipeline_outputs/animations")

    
    # Generate test animation
    output_path, success = generator.generate_animation(
        image_path=test_image_path, prompt=test_prompt, seed=42,num_frames=8
    )

    if success:
        print(f"Test successful! Animation saved to: {output_path}")
    else:
        print("Test failed!")


if __name__ == "__main__":
    # You can run this file directly to test the animation generator
    test_animation_generator()
