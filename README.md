# LIVE AI Hackathon

An AI-powered application that generates visual content based on user interests, combining OpenAI's language models with AWS services for image and animation generation.

## Features

- Interactive exploration of user interests
- AI-generated text descriptions and focused deep dives
- Automatic extraction of visual entities from text
- Generation of AI images for key concepts
- Creation of educational animations
- AWS-powered image processing pipeline

## Prerequisites

- Python 3.11+
- OpenAI API key
- AWS account with appropriate credentials
- Required Python packages (see `requirements.txt`)

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/LIVE-AI-2025-Hackathon.git
cd LIVE-AI-2025-Hackathon

# Install dependencies
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the root directory:

```properties
OPENAI_API_KEY=your_openai_api_key
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_DEFAULT_REGION=us-east-1
```

## Usage

Run the main application:

```bash
python main.py
```

Follow the interactive prompts to:
1. Enter your interest topic
2. Choose a specific aspect to explore
3. View generated images and animations

## Project Structure

```
LIVE-AI-2025-Hackathon/
├── main.py                         # Main application entry point
├── InterestExplorer.py            # OpenAI integration for text generation
├── ProcessInterest.py             # Interest processing logic
├── EducationalAnimationPipeline.py # Animation generation pipeline
├── text_to_image.py               # Image generation utilities
├── requirements.txt               # Project dependencies
└── .env                          # Environment variables (not in git)
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE.md file for details.

## Acknowledgments

- OpenAI for providing the GPT API
- AWS Services for image and animation processing
- Contributors and maintainers of the project