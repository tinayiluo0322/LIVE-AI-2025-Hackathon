from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import pandas as pd
from typing import Optional, List, Dict
# Load environment variables
load_dotenv()

# Define the InterestExplorer class
class InterestExplorer:
    def __init__(self, api_key: str):
        """
        Initialize the InterestExplorer with OpenAI API key.
        
        Args:
            api_key (str): Your OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        
    def generate_exploration(self, interest: str, time_to_read: Optional[int] = 1) -> str:
        """
        Generate an exploration of the user's interest using OpenAI API.
        
        Args:
            interest (str): The topic of interest
            time_to_read (int): Desired reading time in minutes (default: 1)
            
        Returns:
            str: Generated text exploration
        """
        # Calculate approximate word count (average reading speed: 250 words/minute)
        word_count = time_to_read * 250
        
        prompt = f"""
        Generate an engaging exploration about {interest}. The response should:
        - Be approximately {word_count} words
        - Be structured in 3-4 clear paragraphs
        - Include specific examples and insights
        - Be informative yet accessible
        - Start with an engaging hook
        - End with a forward-looking conclusion
        - Be written in an enthusiastic, knowledgeable tone
        
        Make sure to:
        - Focus on what makes {interest} fascinating
        - Include some lesser-known aspects
        - Connect it to broader themes or applications
        - Encourage further exploration
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable and engaging writer who creates compelling explorations of various topics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7,
                presence_penalty=0.6,
                frequency_penalty=0.6
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating content: {str(e)}"
    
    def generate_with_focus(self, interest: str, focus_aspect: str) -> str:
        """
        Generate an exploration with a specific focus aspect.
        
        Args:
            interest (str): The main topic of interest
            focus_aspect (str): Specific aspect to focus on (e.g., "history", "future trends", "practical applications")
            
        Returns:
            str: Generated text exploration
        """
        if focus_aspect.lower() == "no":
            return "No problem! Feel free to ask for a focused exploration anytime."

        prompt = f"""
        Create an engaging exploration about {interest}, focusing specifically on {focus_aspect}.
        The response should be around 250 words, structured in clear paragraphs, and provide
        insightful information about how {focus_aspect} relates to {interest}.
        Include specific examples and conclude with thought-provoking ideas for further exploration.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a knowledgeable and engaging writer who creates compelling explorations of various topics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"Error generating content: {str(e)}"
        

    def potential_entities(self, text: str, interest: str) -> List[Dict[str, str]]:
        """
        Extract potential physical entities from generated text that would be suitable for visual representation.
        
        Args:
            text (str): The generated text from generate_exploration or generate_with_focus
            interest (str): The original interest topic for context
            
        Returns:
            List[Dict[str, str]]: List of 3 entities with their descriptions and relevance scores
        """
        prompt = f"""
        Analyze the following text about {interest} and identify 3 physical entities (objects, places, or things) 
        that would be most suitable for visual representation (images or videos). For each entity:
        1. It must be something that can be clearly visualized
        2. It should be strongly related to the topic
        3. It should be specific rather than abstract
        
        Text to analyze: {text}

        Return a JSON object with an 'entities' array containing exactly 3 objects with these properties:
        - name: The specific name of the entity
        - description: A brief, clear description focusing on visual aspects
        - relevance: Why this entity is important to understanding {interest}

        Ensure all entities are concrete, physical things that could be photographed or filmed.
        """

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying concrete, visual elements from text that would be suitable for image or video creation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.5,
                response_format={ "type": "json_object" }
            )
            
            # Parse the JSON response
            content = eval(response.choices[0].message.content)
            return content['entities']

        except Exception as e:
            return [{"error": f"Error extracting entities: {str(e)}"}]

if __name__ == "__main__":
    # Replace with your OpenAI API key
    API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Initialize the explorer
    explorer = InterestExplorer(API_KEY)
    # Create empty dictionary to store results
    results = {
        'interest': [],
        'basic_exploration': [],
        'focus_aspect': [],
        'focused_exploration': [],
        'entities': []
    }
    # Get user input
    interest = input("What's your interest? ")
    
    # Generate basic exploration
    print("\nGenerating exploration...\n")
    exploration = explorer.generate_exploration(interest)
    
    # Optional: Generate focused exploration
    focus = input("\nWould you like to explore a specific aspect? (e.g., history, applications, future trends): ")
    focused_exploration = ""
    entities = []
    
    if focus:
        print("\nGenerating focused exploration...\n")
        focused_exploration = explorer.generate_with_focus(interest, focus)
        
        # Extract potential entities
        print("\nExtracting potential entities for visualization...\n")
        entities = explorer.potential_entities(focused_exploration, interest)
    
    # Add results to dictionary
    results['interest'].append(interest)
    results['basic_exploration'].append(exploration)
    results['focus_aspect'].append(focus)
    results['focused_exploration'].append(focused_exploration)
    results['entities'].append(json.dumps(entities))  # Convert list to JSON string
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Display the DataFrame
    print("\nStructured Results:")
    
    # Optionally save to CSV
    df.to_csv(f'exploration_{interest.lower().replace(" ", "_")}.csv', index=False)
    print(df)