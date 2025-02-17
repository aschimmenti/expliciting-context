import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from llama_client import llama_client
from json_repair import repair_json


QUESTION_SETS = {
    "BIRTH": [
        "Who was born?",
        "When did the birth occur? (Please provide the date in DD/MM/YYYY format, or just the year if the exact date is not available)",
        "Where did the birth take place? (Provide a description of the location if available)",
        "List all participants, specifying their names and roles, such as 'newborn' or 'parent'",
        "Can you provide a short description for this event? (e.g., 'Birth of Enrico Berlinguer')",
        """ 
    In 1945, Enrico Berlinguer was born in the town of Sassari, located in Sardinia, Italy. He was born into a family deeply involved in politics, which later influenced his political career.
    Gold Standard Answers:
    1. Enrico Berlinguer.
    2. The birth occurred in 1945. The exact date is not specified in the text.
    3. The birth took place in Sassari, Sardinia, Italy.
    4. Participants: Enrico Berlinguer (newborn), his parents (parents).
    5. Birth of Enrico Berlinguer in Sassari, Sardinia, in 1945.
    """,
    ],
    "EDUCATION": [
        "Who is studying or being educated? Where? For how long? Is the subject receiving multiple educations in different places? If so, answer the following questions separately.",
        "When did the subject receive their education? Provide the start and end dates or a specific date if the range is not available.",
        "Where did the education take place? Provide the locations and any descriptions of the institutions or places involved.",
        "Who participated in the education of the subject? List the participants and their roles, such as 'student', 'teacher', or 'other'.",
        "What institutions were involved in the educational event? (Provide details about the institutions or organizations, if available.)",
        "Can you provide a short description for this event(s)? (e.g., 'Enrico Berlinguer's Education')",
        """          Enrico Berlinguer studied at the University of Pisa, where he earned a degree in law. His time at the university greatly shaped his ideological stance, influencing his future work in politics.
    Gold Standard Answers:
    1. Enrico Berlinguer studied at the University of Pisa.
    2. He received his education in the early 1940s, though the exact dates are not specified.
    3. The education took place at the University of Pisa in Pisa, Italy.
    4. Participants: Enrico Berlinguer (student), professors at the University of Pisa (teachers).
    5. The University of Pisa was the main institution involved.
    6. Enrico Berlinguer's education at the University of Pisa, which shaped his future political career.""",
    ],
    "EMPLOYMENT": [
        "Who was employed? Where? For how long? If the subject has had multiple employments, answer the following questions separately.",
        "When did the employment occur? (Provide the start and end dates in DD/MM/YYYY format, or just the year if the exact date is not available)",
        "Where did the employment take place? Provide the locations and any descriptions of the workplaces involved.",
        "List all participants, specifying their names and roles, such as 'employee', 'employer', or 'supervisor'.",
        "What institutions or organizations were involved in the employment? (Provide details about the employers or companies, if available.)",
        "Can you provide a short description for this event(s)? (e.g., 'Enrico Berlinguer's employment at the Italian Communist Party')",
        """ 
    After completing his studies, Enrico Berlinguer worked for the Italian Communist Party (PCI). He served in various roles, gradually rising to the position of General Secretary in 1972.
    Gold Standard Answers:
    1. Enrico Berlinguer was employed by the Italian Communist Party (PCI).
    2. He began his employment with the PCI in the late 1940s and continued through the 1970s. His tenure as General Secretary started in 1972.
    3. His employment took place in various locations, primarily in Italy, including the headquarters of the PCI.
    4. Participants: Enrico Berlinguer (employee), members of the PCI (colleagues).
    5. The Italian Communist Party (PCI) was the primary organization involved.
    6. Enrico Berlinguer's employment at the Italian Communist Party, including his role as General Secretary.
    """,
    ],
    "RELATIONSHIP": [
        "Who formed a relationship?",
        "Which type of relationship? Friendship, marriage, companionship, political alliance, etc.",
        "When did this relation start? (Please provide the date in DD/MM/YYYY format, or just the year if the exact date is not available)",
        "Where did the relationship take place? (Provide a description of the location if available)",
        "List all participants, specifying their names and roles, such as 'spouse', 'friend', 'partner', 'political ally', etc.",
        "Can you provide a short description for this event? (e.g., 'Political alliance between Enrico Berlinguer and the Italian Socialist Party')",
        """ 
    Enrico Berlinguer had a long-lasting and deeply committed relationship with his wife, Livia. They married in the 1950s and shared a life both personally and politically, with Livia being a supportive figure throughout his career.
    Gold Standard Answers:
    1. Enrico Berlinguer and his wife, Livia.
    2. The relationship was a marriage.
    3. The relationship began in the 1950s. The exact date of marriage is not specified in the text.
    4. The relationship took place primarily in Italy, in both private and public settings.
    5. Participants: Enrico Berlinguer (husband), Livia (wife).
    6. Marriage between Enrico Berlinguer and Livia in the 1950s.
    """,
    ],
    "POLITICS": [
"Who were the participants in this event? For each participant, specify their name, type (person/organization/group), and role.",
"When did the event take place? Provide the start and end dates.",
"Where did the event occur? List the location names and descriptions.",
"What was the specific action or event that took place?",
"Provide a brief description of the overall political event.",
"""In 1973, Enrico Berlinguer, the General Secretary of the Italian Communist Party (PCI), gave a historic speech at the party’s annual congress in Florence. This speech, widely regarded as a turning point for the PCI, laid out his vision for Italy's future, advocating for closer ties between the communists and the socialists. It also included strong criticism of the government’s handling of the economy and social issues, as well as a call for greater autonomy from Moscow. The speech was well-received by members of the PCI and the Socialist Party, though it was opposed by some factions within the party, particularly those who favored a more moderate stance. His speech marked a significant step in his leadership and influence over the left-wing politics in Italy.""",
        """Gold Standard Answers:
1. Enrico Berlinguer (General Secretary of the Italian Communist Party), members of the Italian Communist Party (PCI), and members of the Italian Socialist Party (PSI).
2. The political activity occurred in 1973, during the PCI’s annual congress in Florence. The exact date of the speech is not specified in the text.
3. The political activity took place at the PCI’s annual congress, held in Florence, Italy.
4. Berlinguer’s speech was supported by members of the PCI and PSI, but opposed by moderate factions within the PCI.
5. The Italian Communist Party (PCI), led by Enrico Berlinguer, and the Italian Socialist Party (PSI), with whom Berlinguer advocated for closer ties. The Soviet Union (Moscow) is criticized in the speech.
6. Enrico Berlinguer’s speech at the PCI’s 1973 congress in Florence, advocating for stronger ties with the Socialist Party and criticizing the Italian government and Soviet influence.""",
    ],
    "DOCUMENT": [
        "Who created the document?",
        "When was the document created? (Please provide the date in DD/MM/YYYY format, or just the year if the exact date is not available)",
        "Where was the document created or published? (Provide a description of the location if available)",
        "List all participants, specifying their names and roles, such as 'author', 'publisher', or 'contributor'.",
        "What type of document is it? (Provide details about the format, content type, and purpose)",
        "Can you provide a short description for this document? (e.g., 'Enrico Berlinguer's political manifesto on Marxism')",
        """ 
    In 1974, Enrico Berlinguer published a manifesto in which he outlined his vision for the future of Italy, emphasizing the importance of socialist ideals and the need for the working class to unite. The manifesto was widely circulated within the PCI and the broader left-wing political movement.
    Gold Standard Answers:
    1. Enrico Berlinguer created the document.
    2. The document was created in 1974.
    3. The document was published in Italy, though the exact location is not mentioned.
    4. Participants: Enrico Berlinguer (author), members of the PCI (readers).
    5. The document was a political manifesto, focusing on socialist ideals and working-class unity.
    6. Enrico Berlinguer's political manifesto on socialism and the future of Italy.
    """,
    ],
    "DEATH": [
        "Who died?",
        "When did the death occur? (Please provide the date in DD/MM/YYYY format, or just the year if the exact date is not available)",
        "Where did the death take place? (Provide a description of the location if available)",
        "List all participants, specifying their names and roles, such as 'deceased', 'witness', or 'medical personnel'",
        "Can you provide a short description for this event? (e.g., 'Death of Enrico Berlinguer')",
        """ 
    Enrico Berlinguer passed away on June 11, 1984, after suffering a stroke. His death marked the end of an era for the PCI, as he was one of its most prominent leaders. His passing was mourned by many across Italy, with tributes pouring in from political leaders and citizens alike.
    Gold Standard Answers:
    1. Enrico Berlinguer.
    2. The death occurred on June 11, 1984.
    3. The death took place in Rome, Italy.
    4. Participants: Enrico Berlinguer (deceased), medical personnel (attended to him).
    5. The death of Enrico Berlinguer on June 11, 1984, after suffering a stroke.
    """,
    ],
}


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Event:
    type: str
    text: str
    data: Dict
    confidence: float = 0.0


class BiographyProcessor:
    def __init__(self, schema_path: str, examples_path: str = "examples.json"):
        with open(schema_path) as f:
            self.schemas = json.load(f)
        with open(examples_path) as f:
            self.examples = json.load(f)["examples"]
        self.events = []

    def process_paragraph(
        self, text: str, prev_context: str = "", next_context: str = ""
    ) -> List[Event]:
        # 1. Classify paragraph with confidence filtering
        event_classifications = self._classify_paragraph(
            text, prev_context, next_context
        )
        if not event_classifications:
            logger.info(
                "No high-confidence classifications found for this paragraph. Skipping extraction."
            )
            return []  # Skip further processing for this paragraph.

        # 2. Extract events for each high-confidence type
        paragraph_events = []
        for event in event_classifications:
            event_type = event["type"]
            confidence = event["confidence"]
            logger.info(
                f"Processing event type: {event_type} with confidence {confidence}"
            )

            events = self._extract_events(text, event_type, prev_context, next_context)
            paragraph_events.extend(events)

        self.events.extend(paragraph_events)
        return paragraph_events

    def _classify_paragraph(
        self, text: str, prev_context: str, next_context: str
    ) -> List[dict]:
        confidence_threshold = 0.5
        prompt = f"""The following text contains a snippet of the biography of Andrea Costa. 
        Classify the text depending on what's being discussed. 
        Use one or more of the following classes and return the JSON array of classification. 
        The event must be categorized indipendently of whether the event is happening to Andrea Costa or to someone mentioned in his biography.
        BIRTH: the birth of one or more humans. For example, the birth of Andrea Costa, the birth of person who is close to him, etc. 
        RELATIONSHIP: any relationship between two humans; friendship; friendly collaboration; the marriage of one or more humans. Not relatives (e.g. becoming a dad of a child). For example, the marriage of two people, two people becoming friends; of Andrea Costa, etc. 
        EDUCATION: the education and upbringing of a person. Going to school, university, studying somewhere or with someone. 
        EMPLOYMENT: the employment of someone or someone working at a specific thing. For example, going to work for a new contractor; working on a new project; working on a book. 
        POLITICS: the political activity of someone or of a group. For example, the birth of a movement, the failure of a party, election, Andrea Costa being elected.  
        DOCUMENT: the creation of a document, an artifact, or other relevant creation. For example, Andrea Costa writing a book.
        DEATH: the death of an entity. For example, Andrea Costa's death, a close friend's, etc.
        Text: {text}

        Return only a JSON array of classifications. If no proper classification is possible, return any class with 0.0 confidence. 
        [{{"type": "EVENT_TYPE", "confidence": 0.0-1.0, "reason": "explanation"}}]
        """

        try:
            response = llama_client.chat.completions.create(
                model="llama3.3-70b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1000,
                response_format={"type": "json_object"},
            )

            # Extract content from response properly
            content = response.choices[0].message.content
            logger.info(f"Raw response content: {content}")

            # Parse the JSON content
            classifications = json.loads(repair_json(content))

            # Ensure we have a list of classifications
            if isinstance(classifications, dict):
                # If we got a dict with a key containing the array, try to get it
                for key in classifications:
                    if isinstance(classifications[key], list):
                        classifications = classifications[key]
                        break
                # If we still have a dict, wrap it in a list
                if isinstance(classifications, dict):
                    classifications = [classifications]

            # Filter by confidence threshold
            filtered_classifications = [
                c
                for c in classifications
                if isinstance(c, dict) and c.get("confidence", 0) > confidence_threshold
            ]

            logger.info(f"Filtered classifications: {filtered_classifications}")
            return filtered_classifications

        except Exception as e:
            logger.error(f"Classification failed: {str(e)}", exc_info=True)
            return []

    def _extract_events(
        self, text: str, event_type: str, prev_context: str, next_context: str
    ) -> List[Event]:
        schema = self.schemas.get(event_type)
        if not schema:
            return []

        questions = QUESTION_SETS.get(event_type, [])
        if not questions:
            logger.warning(f"No questions defined for event type: {event_type}")
            return []

        # Get the type-specific instructions
        event_instructions = schema.get("instruction", schema.get("instructions", ""))

        # Prompt 1: Ask questions about the text
        question_prompt = f"""
        The following text has been classified as describing a '{event_type}' event in Andrea Costa's life.

        ### Context:
        EVENT TYPE: {event_type}
        - **Previous context:** {prev_context or 'None'}
        - **Target text:** {text}
        - **Following context:** {next_context or 'None'}

        ### Instructions:
        1. Read the questions carefully, and only answer the questions with information relevant for the {event_type} context. 
        2. Read the **target text** with the utmost attention, as it contains the primary information you need.
        2. If there are more than one event described, return the information for each event separately.

        3. Use the additional context (previous and following) only as supplementary information when the target text alone does not provide clarity.
        4. Each event is to be considered as a single situation in which there are participants. If there are multiple situations happening, describe them as separate events.
        5. Assume the event involves Andrea Costa if no explicit subject is mentioned in the target text.

        ### Questions and examples:
        {chr(10).join(f'- {q}' for q in questions)}
        
        
        ### Requirements:
        - Provide concise, direct answers to each question in the order listed.
        - Focus on entities, dates, their actions and only answer the questions from the {event_type} sections of the text. For example:
        - Avoid speculation or assumptions not supported by the provided text.
        - Use dates in **DD/MM/YYYY** format or state the year if precise dates are unavailable.
        - Highlight the specific relations between entities, institutions, and other places if any.
        """

        try:
            response_questions = llama_client.chat.completions.create(
                model="llama3.3-70b",
                messages=[{"role": "user", "content": question_prompt}],
                temperature=0.0,
                max_tokens=2500,
            )
            answers = response_questions.choices[0].message.content
            logger.info(answers)

        except Exception as e:
            logger.error(f"Questionnaire failed for {event_type}: {e}")
            return []

        examples = [ex for ex in self.examples if ex["event"]["type"] == event_type]

        # If no examples are found, log a warning and return empty list
        if not examples:
            logger.warning(f"No examples found for event type: {event_type}")
            return []

        # Limit the number of examples to 3
        examples = examples[:3]

        # Modify the json_prompt to include the examples in the required format
        examples_text = "\n\n".join(
            [
                f"Example {i+1}:\nInput Text:\n{ex['input_text']}\nCorresponding JSON Output:\n{json.dumps(ex['event'], indent=2)}"
                for i, ex in enumerate(examples)
            ]
        )

        # Now, in the json_prompt, instead of one example, include the multiple examples
        json_prompt = f"""
        You are an expert Text-to-JSON agent, tasked with generating structured data for the '{event_type}' JSON schema provided.

        Type-Specific Instructions for {event_type}:
        {event_instructions}

        Context:
        An expert has analyzed a section of Andrea Costa's biography and answered questions about it. Your job is to summarize this text into JSON objects (one for each of the described events) that follow the schema and the type-specific instructions above.

        Key Guidelines:
        2. "Participants" refer to the individuals involved in the individual event. Do not conflate multiple situations into a single event.
        3. If data for a field is unavailable, use null.
        4. Do not add any attributes, comments, or keys beyond what is defined in the schema.
        5. Keep the original italian language for entity labels (e.g. "Socialisti", not "Socialists").

        Examples:
        {examples_text}

        Your Task:
        - Follow the schema using the provided information
        - Generate JSON objects for each event described in the text

        OUTPUT EXPECTATIONS:
        - Return **only** a valid JSON array of events.
        - Ensure the output is strictly compliant with the provided schema.
        - DO NOT CHANGE KEYS, EVEN WHEN THEY DO NOT SEEM ENOUGH.
        - If the text below contain comments or other data that is not required by the schema, do not insert it in the output. 
        - Information from the text that does not fit the schema is not important. 
        
        INPUT TEXT: 
        {answers}

        SCHEMA:
        {json.dumps(schema['properties'], indent=2)}

        YOUR ANSWER:
        """

        try:
            response_json = llama_client.chat.completions.create(
                model="llama3.3-70b",
                messages=[{"role": "user", "content": json_prompt}],
                temperature=0.2,
                max_tokens=15000,
                response_format={"type": "json_object"},
            )

            json_content = response_json.choices[0].message.content
            repaired_json = repair_json(json_content, ensure_ascii=False)
            extracted = json.loads(repaired_json)

            if isinstance(extracted, dict):
                extracted = [extracted]
            elif not isinstance(extracted, list):
                logger.error(f"Unexpected JSON structure: {type(extracted)}")
                return []

            events = []
            for data in extracted:
                if isinstance(data, dict):
                    event = Event(type=event_type, text=text, data=data)
                    events.append(event)
                else:
                    logger.warning(f"Skipping invalid event data: {data}")

            return events

        except Exception as e:
            logger.error(
                f"API request failed for JSON conversion: {str(e)}", exc_info=True
            )
            return []

    def get_relevant_history(self, num_events: int = 5) -> str:
        if not self.events:
            return "None"

        # Convert Event objects to dictionaries
        events_as_dicts = [
            {"type": e.type, "text": e.text, "data": e.data, "confidence": e.confidence}
            for e in self.events[-num_events:]
        ]
        return json.dumps(events_as_dicts, indent=2)


def process_biography(text: str, schema_path: str, output_path: str) -> None:
    processor = BiographyProcessor(schema_path)
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]

    results = []  # Store results for all paragraphs
    for i, paragraph in enumerate(paragraphs):
        prev_context = paragraphs[i - 1] if i > 0 else ""
        next_context = paragraphs[i + 1] if i < len(paragraphs) - 1 else ""

        # Process the current paragraph
        events = processor.process_paragraph(
            text=paragraph, prev_context=prev_context, next_context=next_context
        )

        # Append result per paragraph, regardless of classification outcome
        results.append(
            {
                "paragraph_index": i,
                "paragraph_text": paragraph,
                "events": [
                    {"type": e.type, "text": e.text, "data": e.data} for e in events
                ],
            }
        )

    # Save the results to a JSON file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Processed results saved to {output_path}")


# Usage
if __name__ == "__main__":
    with open("AndreaCostaBio.txt", encoding="utf-8") as f:
        text = f.read()

    events = process_biography(text, "event_schema.json", "output.json")
    print(json.dumps(events, indent=2))
