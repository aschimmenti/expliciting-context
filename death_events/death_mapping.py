from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import json
from datetime import datetime
import os

# Define namespaces
RICO = Namespace("https://www.ica.org/standards/RiC/ontology#")
EX = Namespace("http://example.org/")

def create_uri_safe_string(text):
    """Create a URI-safe string by removing special characters and spaces."""
    if not text is None:
        return text.lower().replace(" ", "_").replace("'", "").replace(",", "")\
                         .replace(".", "").replace("(", "").replace(")", "")\
                         .replace("/", "_")
    return None

def parse_date(date_str):
    """Parse different date formats into ISO format."""
    if not date_str:
        return None
    try:
        if "/" in date_str:
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"
        if "-" in date_str:
            return date_str
        return None
    except ValueError:
        return None

def create_death_graph(event, counter):
    """Create an RDF graph for a death event."""
    g = Graph()
    g.bind("rico", RICO)
    g.bind("ex", EX)
    
    # Process each death record in the event
    for participant in event["data"]["participants"]:
        # Create URIs for the person
        person_uri = EX[f"person/{create_uri_safe_string(participant['name'])}"]
        
        # Add person information
        g.add((person_uri, RDF.type, RICO.Person))
        g.add((person_uri, RICO.name, Literal(participant['name'])))
        
        # Add death date if available
        if participant.get("deathDate"):
            death_date = parse_date(participant["deathDate"])
            if death_date:
                g.add((person_uri, RICO.deathDate, Literal(death_date, datatype=XSD.date)))
        
        # Add death location if available
        if participant.get("deathLocation") and participant["deathLocation"].get("label"):
            place_uri = EX[f"place/{create_uri_safe_string(participant['deathLocation']['label'])}"]
            g.add((place_uri, RDF.type, RICO.Place))
            g.add((place_uri, RICO.name, Literal(participant["deathLocation"]["label"])))
            g.add((person_uri, RICO.hasDeathPlace, place_uri))
            
            if participant["deathLocation"].get("description"):
                g.add((place_uri, RICO.description, 
                      Literal(participant["deathLocation"]["description"])))
        
        # Create death event
        event_uri = EX[f"event/death_{create_uri_safe_string(participant['name'])}_{counter}"]
        g.add((event_uri, RDF.type, RICO.Event))
        g.add((event_uri, RICO.name, 
               Literal(f"Death of {participant['name']}")))
        
        # Add event description
        if event["data"].get("description"):
            g.add((event_uri, RICO.description, 
                  Literal(event["data"]["description"])))
        
        # Add death reason if available
        if participant.get("reason"):
            g.add((event_uri, RICO.description, 
                  Literal(f"Cause of death: {participant['reason']}")))
        
        # Link person to death event
        g.add((event_uri, RICO.hasOrHadParticipant, person_uri))
        
    return g

def convert_death_events_to_rdf(json_data, output_dir="output"):
    """Convert death events from JSON to RDF and save as Turtle files."""
    os.makedirs(output_dir, exist_ok=True)
    counter = 1
    
    for entry in json_data:
        for event in entry["events"]:
            if event["type"] == "DEATH":
                try:
                    g = create_death_graph(event, counter)
                    output_file = os.path.join(output_dir, f"death_event_{counter}.ttl")
                    g.serialize(destination=output_file, format="turtle")
                    counter += 1
                except Exception as e:
                    print(f"Error processing event {counter}: {str(e)}")

if __name__ == "__main__":
    # Read input JSON file
    with open("death_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert events to RDF
    convert_death_events_to_rdf(data)