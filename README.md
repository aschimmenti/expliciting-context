# Archival Biography RiC-O Extraction (ABRE)
A framework for extracting structured information from archival finding aids using Large Language Models.
## Overview
ACE is a pipeline designed to transform unstructured biographical and historical notes from archival finding aids into structured, machine-readable formats. It uses open-source LLMs to identify and extract key events, relationships, and contextual information while maintaining archival description standards.
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

## Requirements
- Python 3.8+
- Any OpenAI-compatible LLM API (currently using LLama3.3-70B) 

## Evaluation
Current performance metrics over Andrea Costa's biography:
Precision: 0.947
Recall: 0.982
F1 Score: 0.964

## Citation
Soon

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
