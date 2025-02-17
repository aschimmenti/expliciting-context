from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import json
from datetime import datetime
import os

RICO = Namespace("https://www.ica.org/standards/RiC/ontology#")
EX = Namespace("http://example.org/#")

def create_uri_safe_string(text):
    if not text:
        return None
    return text.replace(" ", "_").replace("'", "").replace(",", "").replace(".", "")\
               .replace("(", "").replace(")", "").replace("/", "_").lower()

def parse_date(date_str):
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

def create_employment_graph(event, counter):
    g = Graph()
    g.bind("rico", RICO)
    g.bind("ex", EX)

    # Track created positions to avoid duplicates
    created_positions = set()

    for emp in event["data"]["employment"]:
        # Create URIs for person
        person_uri = EX[f"person/{create_uri_safe_string(emp['name'])}"]

        # Add person information
        g.add((person_uri, RDF.type, RICO.Person))
        g.add((person_uri, RICO.name, Literal(emp['name'])))

        # Process each organization the person works for
        for org in emp["worksFor"]:
            # Create URIs for organization and position
            org_uri = EX[f"corporatebody/{create_uri_safe_string(org['name'])}"]
            
            # Create position identifier
            position_id = f"{create_uri_safe_string(emp['role'])}_{create_uri_safe_string(org['name'])}"
            
            # Only create position if it doesn't exist
            if position_id not in created_positions:
                position_uri = EX[f"position/{position_id}"]
                g.add((position_uri, RDF.type, RICO.Position))
                g.add((position_uri, RICO.name, Literal(emp['role'])))
                g.add((position_uri, RICO.existsOrExistedIn, org_uri))
                created_positions.add(position_id)
            else:
                position_uri = EX[f"position/{position_id}"]

            # Add organization information
            g.add((org_uri, RDF.type, RICO.CorporateBody))
            g.add((org_uri, RICO.name, Literal(org['name'])))
            if org.get('type'):
                g.add((org_uri, RICO.corporateBodyType, Literal(org['type'])))

            # Create position holding relation
            relation_id = f"{create_uri_safe_string(emp['name'])}_{create_uri_safe_string(emp['role'])}_{counter}"
            relation_uri = EX[f"positionHoldingRelation/{relation_id}"]
            g.add((relation_uri, RDF.type, RICO.PositionHoldingRelation))
            g.add((relation_uri, RICO.relationHasSource, person_uri))
            g.add((relation_uri, RICO.relationHasTarget, position_uri))

            # Add dates if available
            if emp["date"].get("startDate"):
                start_date = parse_date(emp["date"]["startDate"])
                if start_date:
                    g.add((relation_uri, RICO.beginningDate, Literal(start_date, datatype=XSD.date)))
            
            if emp["date"].get("endDate"):
                end_date = parse_date(emp["date"]["endDate"])
                if end_date:
                    g.add((relation_uri, RICO.endDate, Literal(end_date, datatype=XSD.date)))

            # Add location if available
            if emp.get("location") and emp["location"].get("label"):
                place_uri = EX[f"place/{create_uri_safe_string(emp['location']['label'])}"]
                g.add((place_uri, RDF.type, RICO.Place))
                g.add((place_uri, RICO.name, Literal(emp["location"]["label"])))
                g.add((org_uri, RICO.isLocatedAt, place_uri))
                
                if emp["location"].get("description"):
                    g.add((place_uri, RICO.description, Literal(emp["location"]["description"])))

    return g

def convert_employment_events_to_rdf(json_data, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    counter = 1

    for entry in json_data:
        for event in entry["events"]:
            if event["type"] == "EMPLOYMENT":
                try:
                    g = create_employment_graph(event, counter)
                    output_file = os.path.join(output_dir, f"employment_event_{counter}.ttl")
                    g.serialize(destination=output_file, format="turtle")
                    counter += 1
                except Exception as e:
                    print(f"Error processing event {counter}: {str(e)}")

if __name__ == "__main__":
    with open("employment_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    convert_employment_events_to_rdf(data)