from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import json
from datetime import datetime
import os

RICO = Namespace("https://www.ica.org/standards/RiC/ontology#")
EX = Namespace("http://example.org/#")

def create_uri_safe_string(text):
    """Create a URI-safe string by removing special characters and spaces."""
    if not text:
        return None
    return text.replace(" ", "_").replace("'", "").replace(",", "").replace(".", "") \
              .replace("(", "").replace(")", "").replace("/", "_").lower()

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

def create_political_situation_graph(event, counter):
    """Create an RDF graph for a political situation."""
    g = Graph()
    g.bind("rico", RICO)
    g.bind("ex", EX)

    # Create the main Activity (Situation)
    activity_id = create_uri_safe_string(event["data"]["description"])
    activity_uri = EX[f"activity_{activity_id}_{counter}"]
    g.add((activity_uri, RDF.type, RICO.Activity))
    g.add((activity_uri, RICO.name, Literal(event["data"]["description"])))

    # Add the action type if available
    if "actions" in event["data"]["properties"] and event["data"]["properties"]["actions"]:
        action = event["data"]["properties"]["actions"][0]
        if "action" in action:
            activity_type_id = create_uri_safe_string(action['action'])
            activity_type_uri = EX[f"activity_type_{activity_type_id}"]
            g.add((activity_type_uri, RDF.type, RICO.ActivityType))
            g.add((activity_type_uri, RICO.name, Literal(action['action'])))
            g.add((activity_uri, RICO.hasActivityType, activity_type_uri))

        # Process dates
        if "date" in action:
            if action["date"].get("startDate"):
                start_date = parse_date(action["date"]["startDate"])
                if start_date:
                    g.add((activity_uri, RICO.beginningDate, 
                          Literal(start_date, datatype=XSD.date)))
            
            if action["date"].get("endDate"):
                end_date = parse_date(action["date"]["endDate"])
                if end_date:
                    g.add((activity_uri, RICO.endDate, 
                          Literal(end_date, datatype=XSD.date)))

        # Process participants and their roles
        if "participants" in action:
            for participant in action["participants"]:
                # Create participant entity
                participant_name = create_uri_safe_string(participant['name'])
                participant_uri = EX[participant_name]
                
                # Add type based on participant category
                if participant['type'] == 'person':
                    g.add((participant_uri, RDF.type, RICO.Person))
                elif participant['type'] in ['organization', 'group']:
                    g.add((participant_uri, RDF.type, RICO.CorporateBody))
                
                # Add participant name
                g.add((participant_uri, RICO.name, Literal(participant['name'])))
                
                # Create PerformanceRelation
                performance_id = f"{participant_name}_{activity_id}_{counter}"
                relation_uri = EX[performance_id]
                g.add((relation_uri, RDF.type, RICO.PerformanceRelation))
                g.add((relation_uri, RICO.relationHasSource, activity_uri))
                g.add((relation_uri, RICO.relationHasTarget, participant_uri))
                
                # Add role description if available
                if 'role' in participant:
                    g.add((relation_uri, RICO.description, Literal(participant['role'])))

        # Process locations
        if "location" in action:
            for location in action["location"]:
                if location.get("label"):
                    place_id = create_uri_safe_string(location['label'])
                    place_uri = EX[f"place_{place_id}"]
                    g.add((place_uri, RDF.type, RICO.Place))
                    g.add((place_uri, RICO.name, Literal(location["label"])))
                    
                    if location.get("description"):
                        g.add((place_uri, RICO.description, Literal(location["description"])))
                    
                    # Create PlaceRelation
                    place_relation_id = f"{place_id}_{activity_id}_{counter}"
                    place_relation_uri = EX[place_relation_id]
                    g.add((place_relation_uri, RDF.type, RICO.PlaceRelation))
                    g.add((place_relation_uri, RICO.relationHasSource, place_uri))
                    g.add((place_relation_uri, RICO.relationHasTarget, activity_uri))

    return g

def convert_political_events_to_rdf(json_data, output_dir="output"):
    """Convert political events from JSON to RDF and save as Turtle files."""
    os.makedirs(output_dir, exist_ok=True)
    counter = 1

    for entry in json_data:
        for event in entry["events"]:
            if event["type"] == "POLITICS":
                try:
                    g = create_political_situation_graph(event, counter)
                    output_file = os.path.join(output_dir, f"political_event_{counter}.ttl")
                    g.serialize(destination=output_file, format="turtle")
                    print(f"Created: {output_file}")
                    counter += 1
                except Exception as e:
                    print(f"Error processing event {counter}: {str(e)}")

if __name__ == "__main__":
    with open("politics_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    convert_political_events_to_rdf(data)