from InterestExplorer import InterestExplorer
import os
import pandas as pd
import json

def process_interest(explorer: InterestExplorer) -> dict:
    """
    Process user interest and generate explorations and entities.
    
    Args:
        explorer (InterestExplorer): Initialized InterestExplorer instance
        
    Returns:
        dict: Dictionary containing all results
    """
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
    
    return results


if __name__ == "__main__":
    # Replace with your OpenAI API key
    API_KEY = os.getenv("OPENAI_API_KEY")
    
    # Initialize the explorer
    explorer = InterestExplorer(API_KEY)
    
    # Process interest and get results
    results = process_interest(explorer)
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Display the DataFrame
    print("\nStructured Results:")
    print(df)