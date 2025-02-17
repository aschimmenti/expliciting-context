from rdflib import Graph, Namespace, Literal, URIRef, RDF, XSD
from collections import OrderedDict
import json
from datetime import datetime
import os

RICO = Namespace("https://www.ica.org/standards/RiC/ontology#")
EX = Namespace("http://example.org/#")

def create_uri_safe_string(text):
    if not text:
        return None
    return text.lower().replace(" ", "_").replace("'", "").replace(",", "")\
               .replace(".", "").replace("(", "").replace(")", "")\
               .replace("/", "_")

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

def add_ordered_position_holding_relation(g, person_uri, position_uri, counter, start_date=None, end_date=None):
    """Create standardized position holding relation with ordered properties"""
    person_name = str(person_uri).split('/')[-1]
    position_name = str(position_uri).split('/')[-1].split('_')[0]
    relation_uri = EX[f"positionHoldingRelation/{person_name}_{position_name}_{counter}"]
    
    # Add properties in standard order
    g.add((relation_uri, RDF.type, RICO.PositionHoldingRelation))
    if start_date:
        g.add((relation_uri, RICO.beginningDate, Literal(start_date, datatype=XSD.date)))
    if end_date:
        g.add((relation_uri, RICO.endingDate, Literal(end_date, datatype=XSD.date)))
    g.add((relation_uri, RICO.relationHasSource, person_uri))
    g.add((relation_uri, RICO.relationHasTarget, position_uri))
    
    return relation_uri

def add_teaching_relation(g, teacher_uri, student_uri):
    """Create standardized teaching relation"""
    teacher_name = str(teacher_uri).split('/')[-1]
    student_name = str(student_uri).split('/')[-1]
    relation_uri = EX[f"TeachingRelation/{teacher_name}_{student_name}"]
    
    # Add properties in standard order
    g.add((relation_uri, RDF.type, RICO.TeachingRelation))
    g.add((relation_uri, RICO.relationHasSource, teacher_uri))
    g.add((relation_uri, RICO.relationHasTarget, student_uri))
    
    return relation_uri

def create_education_graph(event, counter):
    g = Graph()
    g.bind("rico", RICO)
    g.bind("ex", EX)
    
    created_positions = {}  # Track positions by institution
    teacher_student_pairs = []
    
    # First pass: Create basic entities and track positions
    for education in event["data"]["education"]:
        # Add person
        person_uri = EX[f"person/{create_uri_safe_string(education['name'])}"]
        g.add((person_uri, RDF.type, RICO.Person))
        g.add((person_uri, RICO.name, Literal(education['name'])))
        
        if education['institution']['name']:
            inst_name = create_uri_safe_string(education['institution']['name'])
            inst_uri = EX[f"institution/{inst_name}"]
            
            # Add institution
            g.add((inst_uri, RDF.type, RICO.CorporateBody))
            g.add((inst_uri, RICO.name, Literal(education['institution']['name'])))
            if education['institution']['type']:
                g.add((inst_uri, RICO.corporateBodyType, Literal(education['institution']['type'])))
            
            # Create position for role in institution
            role = create_uri_safe_string(education['role'])
            position_uri = EX[f"position/{role}_{inst_name}"]
            
            if position_uri not in created_positions:
                g.add((position_uri, RDF.type, RICO.Position))
                g.add((position_uri, RICO.name, Literal(education['role'])))
                g.add((position_uri, RICO.existsOrExistedIn, inst_uri))
                created_positions[position_uri] = inst_uri
            
            # Add position holding relation
            start_date = parse_date(education['period'].get('startDate')) if education.get('period') else None
            end_date = parse_date(education['period'].get('endDate')) if education.get('period') else None
            add_ordered_position_holding_relation(g, person_uri, position_uri, counter, start_date, end_date)
            
            # Track teacher-student relationships
            if education['role'] in ['teacher', 'professor']:
                for student in event["data"]["education"]:
                    if (student['role'] == 'student' and 
                        student['institution']['name'] == education['institution']['name']):
                        teacher_student_pairs.append((person_uri, create_uri_safe_string(student['name'])))
    
    # Second pass: Add teaching relations
    for teacher_uri, student_name in teacher_student_pairs:
        student_uri = EX[f"person/{student_name}"]
        add_teaching_relation(g, teacher_uri, student_uri)
    
    return g

def convert_education_events_to_rdf(json_data, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    counter = 1
    
    for entry in json_data:
        for event in entry["events"]:
            if event["type"] == "EDUCATION":
                try:
                    g = create_education_graph(event, counter)
                    output_file = os.path.join(output_dir, f"education_event_{counter}.ttl")
                    g.serialize(destination=output_file, format="turtle")
                    counter += 1
                except Exception as e:
                    print(f"Error processing event {counter}: {str(e)}")

if __name__ == "__main__":
    with open("education_events.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    convert_education_events_to_rdf(data)