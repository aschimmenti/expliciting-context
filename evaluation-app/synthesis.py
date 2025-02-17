import json

def filter_events_by_type(input_json, event_type):
    """
    Filter events from input JSON based on event type while maintaining paragraph structure.
    Only keeps paragraphs that contain events of the specified type.
    """
    # Parse JSON if it's a string
    if isinstance(input_json, str):
        try:
            data = json.loads(input_json)
        except json.JSONDecodeError:
            print("Error: Invalid JSON string")
            return []
    else:
        data = input_json
        
    filtered_data = []
    
    for paragraph in data:
        # Filter events of specified type
        filtered_events = [
            event for event in paragraph.get('events', [])
            if event.get('type') == event_type
        ]
        
        # If we found events of this type in the paragraph
        if filtered_events:
            # Create new paragraph entry with filtered events
            filtered_paragraph = {
                'paragraph_index': paragraph['paragraph_index'],  # Changed from paragraphindex
                'paragraph_text': paragraph['paragraph_text'],    # Changed from paragraphtext
                'events': filtered_events
            }
            filtered_data.append(filtered_paragraph)
    
    return filtered_data

def create_event_type_files(input_json):
    """
    Create separate JSON files for each event type
    """
    # Define event types based on the JSON structure
    event_types = set()
    # Extract unique event types from the data
    for paragraph in input_json:
        for event in paragraph.get('events', []):
            if 'type' in event:
                event_types.add(event['type'])
    
    result = {}
    for event_type in event_types:
        filtered_data = filter_events_by_type(input_json, event_type)
        # Write to file
        output_filename = f"{event_type.lower()}_events.json"
        with open(output_filename, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        print(f"Created {output_filename}")
        result[event_type.lower()] = filtered_data
    
    return result

# Usage example:
if __name__ == "__main__":
    # For the provided JSON content in the document
    with open('events.json', 'r', encoding='utf-8') as f:
        input_json = json.load(f)
    
    # Create the filtered files
    result = create_event_type_files(input_json)