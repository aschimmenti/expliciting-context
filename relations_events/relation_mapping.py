from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import json
import os
from datetime import datetime

# Define namespaces
RICO = Namespace("https://www.ica.org/standards/RiC/ontology#")
EX = Namespace("http://example.org/")

def create_uri_safe_string(text):
    """Create a URI-safe string from text."""
    return text.replace(" ", "_").replace("'", "").replace(",", "").replace(".", "")

def parse_date(date_str):
    """Parse different date formats and return YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        if "/" in date_str:
            # Handle DD/MM/YYYY format
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        # If only year is provided, use January 1st as default date
        if date_str.isdigit() and len(date_str) == 4:
            return f"{date_str}-01-01"
        return None
    except ValueError:
        return None

def create_relationship_graph(event_data, counter):
    """Create a graph for a single relationship event."""
    g = Graph()
    
    # Bind namespaces
    g.bind("rico", RICO)
    g.bind("ex", EX)
    
    # Extract relationship data
    relation = event_data["relations"][0]
    person1_name = relation["name"]
    person2_name = relation["hasRelationshipWith"][0]["name"]
    
    # Create URIs for entities
    person1_uri = EX[f"person/{create_uri_safe_string(person1_name)}"]
    person2_uri = EX[f"person/{create_uri_safe_string(person2_name)}"]
    relation_uri = EX[f"AgentToAgentRelation/relation_{counter}"]
    
    # Add People
    g.add((person1_uri, RDF.type, RICO.Person))
    g.add((person1_uri, RICO.name, Literal(person1_name)))
    g.add((person1_uri, RICO.thigIsConnectedToRelation, relation_uri))
    
    g.add((person2_uri, RDF.type, RICO.Person))
    g.add((person2_uri, RICO.name, Literal(person2_name)))
    g.add((person2_uri, RICO.thigIsConnectedToRelation, relation_uri))
    
    # Add Relationship
    g.add((relation_uri, RDF.type, RICO.AgentToAgentRelation))
    g.add((relation_uri, RICO.relationConnects, person1_uri))
    g.add((relation_uri, RICO.relationConnects, person2_uri))
    
    # Add relationship type based on roles
    rel_type = None
    if relation["role"] == "husband" or relation["role"] == "wife":
        rel_type = "marriage"
    elif relation["role"] == "partner":
        rel_type = "romantic relation"
    elif relation["role"] == "political ally":
        rel_type = "political alliance"
    
    if rel_type:
        g.add((relation_uri, RICO.type, Literal(rel_type)))
    
    # Add dates
    start_date = parse_date(relation["date"]["startDate"])
    end_date = parse_date(relation["date"]["endDate"])
    
    if start_date:
        g.add((relation_uri, RICO.beginningDate, Literal(start_date, datatype=XSD.date)))
    if end_date and end_date != start_date:  # Only add end date if different from start date
        g.add((relation_uri, RICO.endDate, Literal(end_date, datatype=XSD.date)))
    
    # Add location if available
    if relation["location"]["label"]:
        location_uri = EX[f"place/{create_uri_safe_string(relation['location']['label'])}"]
        g.add((location_uri, RDF.type, RICO.Place))
        g.add((location_uri, RICO.name, Literal(relation["location"]["label"])))
        g.add((relation_uri, RICO.hasOrHadLocation, location_uri))
        g.add((location_uri, RICO.isOrWasLocationOf, relation_uri))
    
    # Add description as name of the relation
    g.add((relation_uri, RICO.name, Literal(event_data["description"])))
    
    return g

def convert_events_to_rdf(json_data, output_dir="output"):
    """Convert all events to RDF and save as separate files."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    counter = 1
    for event in json_data:
        if event["events"][0]["type"] == "RELATIONSHIP":
            event_data = event["events"][0]["data"]
            g = create_relationship_graph(event_data, counter)
            
            # Save to file
            output_file = os.path.join(output_dir, f"relationship_{counter}.ttl")
            g.serialize(destination=output_file, format="turtle")
            counter += 1

# Example usage
if __name__ == "__main__":
    # Read JSON data
    with open("relationship_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert events to RDF
    convert_events_to_rdf(data)