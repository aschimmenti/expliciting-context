# Archival Biography RiC-O Extraction (ABRE)
A framework for extracting structured information from archival finding aids using Large Language Models.
## Overview
ABRE is a (wip) pipeline designed to transform unstructured biographical and historical notes from archival finding aids into structured, machine-readable formats. It uses open-source LLMs to identify and extract key events, relationships, and contextual information while maintaining archival description standards, guaranteed by the aligment of the output to the Records in Contexts Ontology (RiC-O).
## Features

- Event-based information extraction from biographical notes
- Support for 7 event types (Birth, Death, Education, Employment, Relationship, Political, Document)
- JSON Schemas based on the DOLCE foundational ontology
- Integration with Records in Contexts (RiC-O) ontology
- Built-in app for manually assessing extraction quality

## Pipeline Steps
- Event Classification
- Information Extraction
- Schema Validation
- RiC-O Mapping

## How the Code Works

### 1. Event Extraction
The `event_extraction.py` script processes biographical text through the following steps:

- **Text Segmentation**: Divides the input text into paragraphs for processing.
- **Event Classification**: Uses LLM (Llama3.3-70B) to classify each paragraph into one of seven event types (Birth, Death, Education, Employment, Relationship, Politics, Document).
- **Information Extraction**: For each classified paragraph, uses a question-answering approach to extract structured information about the event.
- **JSON Conversion**: Transforms the extracted information into structured JSON according to predefined schemas in `event_schema.json`.

### 2. Schema Validation
The extracted events are validated against JSON schemas defined for each event type, ensuring data consistency and completeness.

### 3. RiC-O Mapping
Each event type has a dedicated mapping script (e.g., `birth_mapping.py`) that:

- Reads the JSON output from the extraction phase
- Creates an RDF graph using the RiC-O ontology
- Maps extracted entities to appropriate RiC-O classes (Person, Place, Event, etc.)
- Establishes relationships between entities using RiC-O properties
- Outputs the resulting graph as TTL (Turtle) files

### 4. Evaluation
The framework includes an evaluation app to assess the quality of the extraction and mapping process, allowing for manual verification and correction.

## Requirements
- Python 3.8+
- Any OpenAI-compatible LLM API (currently using LLama3.3-70B)
- The script event-extraction.py requires a schema file and a .txt file
- Each mapping script is inside the specific folder   

## Evaluation
Current performance metrics over Andrea Costa's biography:
Precision: 0.947
Recall: 0.982
F1 Score: 0.964

## Citation

### APA
Giagnolini, L., Schimmenti, A., Bonora, P., & Tomasi, F. (2025). Expliciting Contexts: Semantic Knowledge Extraction from Traditional Archival Descriptions. Umanistica Digitale, 9(20), 115–144. https://doi.org/10.6092/issn.2532-8816/21229

### BibTeX
```bibtex
@article{giagnolini2025expliciting,
	title        = {
		Expliciting Contexts: Semantic Knowledge Extraction from Traditional Archival
		Descriptions
	},
	author       = {
		Giagnolini, Lucia and Schimmenti, Andrea and Bonora, Paolo and Tomasi,
		Francesca
	},
	year         = 2025,
	journal      = {Umanistica Digitale},
	volume       = 9,
	number       = 20,
	pages        = {115–144},
	DOI          = {10.6092/issn.2532-8816/21229},
	url          = {https://umanisticadigitale.unibo.it/article/view/21229}
}
```

## License
This project is licensed under MIT License
## Acknowledgments
Research partially funded by the European Union - Next Generation EU, investment I.4.1 PNRR Patrimonio Culturale, Decreto Ministeriale n. 351 del 9 aprile 2022.
## Contact
Replace "dhdk" with "unibo.it". This is done to avoid spam from bots. 
- Lucia Giagnolini - lucia.giagnolini2@[dhdk]
- Andrea Schimmenti - andrea.schimmenti2@[dhdk]
- Paolo Bonora - paolo.bonora@[dhdk]
- Francesca Tomasi - francesca.tomasi@[dhdk]
