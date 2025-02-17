from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import json
from datetime import datetime
import os

# Define namespaces
RICO = Namespace("https://www.ica.org/standards/RiC/ontology#")
EX = Namespace("http://example.org/")

def create_uri_safe_string(text):
    """Create a URI-safe string from text."""
    return text.replace(" ", "_").replace("'", "").replace(",", "").replace(".", "").replace("(", "").replace(")", "")

def parse_date(date_str):
    """Parse different date formats and return YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        if "/" in date_str:
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"
        return None
    except ValueError:
        return None

def create_birth_graph(event_data, counter):
    g = Graph()
    g.bind("rico", RICO)
    g.bind("ex", EX)
    
    # Extract data
    newborn = next(p for p in event_data["participants"] if p["role"] == "newborn")
    parents = [p for p in event_data["participants"] if p["role"] == "parent"]
    birth_date = parse_date(newborn.get("birthDate"))
    
    # Create URIs using [] notation
    event_uri = EX[f"event/Birth_{create_uri_safe_string(newborn['name'])}"]
    newborn_uri = EX[f"person/{create_uri_safe_string(newborn['name'])}"]
    date_uri = EX[f"date/{birth_date}"] if birth_date else None
    
    # Create Birth Event
    g.add((event_uri, RDF.type, RICO.Event))
    g.add((event_uri, RICO.name, Literal(event_data["description"])))
    
    # Add newborn
    g.add((newborn_uri, RDF.type, RICO.Person))
    g.add((newborn_uri, RICO.name, Literal(newborn["name"])))
    g.add((event_uri, RICO.hasOrHadParticipant, newborn_uri))
    
    # Add date
    if birth_date:
        g.add((date_uri, RDF.type, RICO.Date))
        g.add((date_uri, RICO.normalizedDateValue, Literal(birth_date, datatype=XSD.date)))
        g.add((event_uri, RICO.occurredAtDate, date_uri))
    
    # Process parents and family relations
    family_uri = EX[f"family/{create_uri_safe_string(newborn['name'])}_Family"]
    g.add((family_uri, RDF.type, RICO.Family))
    g.add((family_uri, RICO.name, Literal(f"{newborn['name']} Family")))
    g.add((family_uri, RICO.hasOrHadMember, newborn_uri))
    
    for parent in parents:
        parent_uri = EX[f"person/{create_uri_safe_string(parent['name'])}"]
        g.add((parent_uri, RDF.type, RICO.Person))
        g.add((parent_uri, RICO.name, Literal(parent["name"])))
        g.add((parent_uri, RICO.hasChild, newborn_uri))
        g.add((newborn_uri, RICO.hasParent, parent_uri))
        g.add((event_uri, RICO.hasOrHadParticipant, parent_uri))
        g.add((family_uri, RICO.hasOrHadMember, parent_uri))
        
        # Create Family Relation
        relation_uri = EX[f"relation/family_{create_uri_safe_string(parent['name'])}_{create_uri_safe_string(newborn['name'])}"]
        g.add((relation_uri, RDF.type, RICO.FamilyRelation))
        g.add((relation_uri, RICO.relationHasSource, parent_uri))
        g.add((relation_uri, RICO.relationHasTarget, newborn_uri))
        g.add((relation_uri, RICO.familyRelationType, Literal("parent-child")))
        if birth_date:
            g.add((relation_uri, RICO.hasBeginningDate, Literal(birth_date, datatype=XSD.date)))
    
    # Add location if available
    if event_data["location"]["label"] and event_data["location"]["label"] != "Unknown Location":
        place_uri = EX[f"place/{create_uri_safe_string(event_data['location']['label'])}"]
        g.add((place_uri, RDF.type, RICO.Place))
        g.add((place_uri, RICO.name, Literal(event_data["location"]["label"])))
        
        # Create Place Relation
        place_relation_uri = EX[f"relation/birth_place_{create_uri_safe_string(newborn['name'])}"]
        g.add((place_relation_uri, RDF.type, RICO.PlaceRelation))
        g.add((place_relation_uri, RICO.relationHasSource, place_uri))
        g.add((place_relation_uri, RICO.relationHasTarget, newborn_uri))
        g.add((place_relation_uri, RICO.placeRelationType, Literal("birthPlace")))
        if birth_date:
            g.add((place_relation_uri, RICO.date, Literal(birth_date, datatype=XSD.date)))
    
    return g

def convert_birth_events_to_rdf(json_data, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    
    counter = 1
    for event in json_data:
        for subevent in event["events"]:
            if subevent["type"] == "BIRTH":
                g = create_birth_graph(subevent["data"], counter)
                output_file = os.path.join(output_dir, f"birth_{counter}.ttl")
                g.serialize(destination=output_file, format="turtle")
                counter += 1

if __name__ == "__main__":
    with open("birth_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    convert_birth_events_to_rdf(data)