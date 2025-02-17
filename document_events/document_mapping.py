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

def create_document_graph(event, counter):
    """Create an RDF graph for a document event."""
    g = Graph()
    g.bind("rico", RICO)
    g.bind("ex", EX)
    
    doc_data = event["data"]["document"]
    
    # Create URI for the document record
    doc_uri = EX[f"record/{create_uri_safe_string(doc_data['title'])}_{counter}"]
    
    # Add basic document information
    g.add((doc_uri, RDF.type, RICO.Record))
    
    g.add((doc_uri, RICO.name, Literal(doc_data['title'])))
    
    # Add document type
    if doc_data.get('contentType'):
        content_type_uri = EX[f"contentType/{create_uri_safe_string(doc_data['contentType'])}"]
        g.add((content_type_uri, RDF.type, RICO.ContentType))
        g.add((content_type_uri, RICO.name, Literal(doc_data['contentType'])))
        g.add((doc_uri, RICO.hasContentOfType, content_type_uri))
    
    # Add creation date if available
    if doc_data.get("creationDate"):
        creation_date = parse_date(doc_data["creationDate"])
        if creation_date:
            g.add((doc_uri, RICO.hasCreationDate, Literal(creation_date, datatype=XSD.date)))
    
    # Process creators and their roles
    for creator in doc_data.get("creator", []):
        # Create URIs for person/organization and their role
        creator_uri = EX[f"agent/{create_uri_safe_string(creator['name'])}"]
        
        # Add creator information
        if "person" in creator.get('type', 'person').lower():
            g.add((creator_uri, RDF.type, RICO.Person))
        else:
            g.add((creator_uri, RDF.type, RICO.CorporateBody))
            
        g.add((creator_uri, RICO.name, Literal(creator['name'])))
        
        # Handle different roles
        if creator['role'].lower() == 'author':
            g.add((doc_uri, RICO.hasOrganicProvenance, creator_uri))
        elif creator['role'].lower() == 'contributor':
            g.add((doc_uri, RICO.hasOrganicProvenance, creator_uri))
            
        # Add agent relation to document
        g.add((creator_uri, RICO.isOrganicProvenanceOf, doc_uri))
    
    return g

def convert_document_events_to_rdf(json_data, output_dir="output"):
    """Convert document events from JSON to RDF and save as Turtle files."""
    os.makedirs(output_dir, exist_ok=True)
    counter = 1
    
    for entry in json_data:
        for event in entry["events"]:
            if event["type"] == "DOCUMENT":
                try:
                    g = create_document_graph(event, counter)
                    output_file = os.path.join(output_dir, f"document_event_{counter}.ttl")
                    g.serialize(destination=output_file, format="turtle")
                    counter += 1
                except Exception as e:
                    print(f"Error processing event {counter}: {str(e)}")

if __name__ == "__main__":
    # Read input JSON file
    with open("document_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Convert events to RDF
    convert_document_events_to_rdf(data)