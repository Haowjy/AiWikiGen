"""This module contains the agent class for to read a single chapter and generate a comprehensive summary and information extraction tasks."""
from pydantic import BaseModel
from typing import Optional

from novelinsights.base.base_agent import BaseAgent
from novelinsights.base.base_llm import LLMWrapper
from qdrant_client import QdrantClient

def task() -> str:
    return """Your task is to produce a comprehensive and detailed summary of the current chapter, as well as extract and organize all significant information into predefined categories: Characters, Chronology, Locations, Organizations, Things, and Concepts. The output should be thorough and suitable for creating Wikipedia-style entries, ensuring that all essential details from the chapter are captured accurately."""

def instructions(prev_chap_context:str = None) -> str:
    instructions = """## Non-Plot Content
- Identify if the chapter is for non-plot content (e.g., front matter, acknowledgments, table of contents, etc.)
- If the chapter is non-plot content, you make skip Information Extraction and replace the content with "<SKIPPED-EXTRACTION>"

## Information Extraction

For each category below, extract relevant details from the chapter. Present the information in a clear and organized manner, using bullet points or numbered lists where appropriate. If the chapter does not contain information for a specific category, you may omit it.

For all items in each category, make sure to explain why you chose them and how they contribute to the plot of the entire story. Rank the importance of each item as very high, high, medium, low, or very low.

### Entities
 - List all important characters introduced or featured in this chapter
 - Provide a detailed description of the character. Include (if available):
 - type of entity (character, monster, abstract force)
 - Name
 - Role in the plot/chapter
 - Personality
 - Relationships with other characters
 - Significance to the plot or characters
 - backstory, motivations, or any other relevant details
 - any other relevant details

### Chronology
 - Identify and list the events that occur or are described in the chapter
 - For each event, provide a detailed description. Include (if available):
 - Name or title of the event
 - Type or category of the event
 - Overarching Conflict name or title
 - Significance to the plot or characters
 - any chronology of the event
 - Background or context leading to the event
 - Characters involved and their roles
 - Locations where the event takes place
 - any other relevant details

### Locations
 - List and describe any important locations introduced or revisited
 - Provide a detailed description of each location. Include (if available):
 - Name of the location
 - significance to the plot or characters
 - physical description or notable features
 - cultural or historical significance
 - any history or background information
 - nearby locations or connections to other places 
 - any other relevant details

### Organizations
 - List any important organizations, groups, or factions mentioned or central to the chapter
 - Provide a detailed description of each organization. Include (if available):
 - Name of the organization
 - Purpose or goals
 - Key members or leaders
 - Relationships with other organizations
 - any significant actions or decisions made by the organization
 - any history or background information
 - any other relevant

### Things
 - List any important items introduced or referenced in the chapter
 - Provide a detailed description of each item. Include (if available):
 - Name of the item
 - Type or category
 - Physical description or notable features
 - Special properties or functions
 - Significance to the plot or characters
 - History or background information
 - Current status or location
 - any related entities or connections
 - any other relevant details

### Concepts
 - List any key concepts, ideas, or themes explored in the chapter
 - Provide a detailed description of each concept. Include (if available):
 - Name or title of the concept
 - Definition or explanation
 - Significance to the plot or characters
 - any examples or instances in the chapter
 - any connections to other concepts or themes
 - any other relevant details

### Story Arc
- Identify and describe the overarching conflict or main storyline based on this chapter and previous context
- Provide a detailed description of the conflict. Include (if available):
    - Proper name or title of the conflict
    - Description of the conflict
    - any history or background information
    - any other relevant details

## General Chapter Summary
- Write a detailed summary of the entire chapter (approximately 300-500 words).
- Focus on key plot developments, character actions and interactions, significant events, and any important revelations.
- Ensure the summary is coherent and logically flows from one point to the next.
- This should not be explicitly for "this chapter" but should be a general summary of the chapter's content."""
    if prev_chap_context is not None: instructions += """## 3. Previous Chapter(s) Summary:
- using the previous chapter context, write a summary of the previous chapter(s) to provide continuity and context for the current chapter."""
    return instructions

def general_reminders() -> str:
    return """- Do not use external knowledge or information beyond what is provided in the chapter and previous context.
- Stick strictly to the information in the chapter context and prior story summaries.
- DO NOT explicitly mention "chapter" or "book" in the response. Instead, refer to the content as if it were a standalone piece of information.
- Make sure to follow the exact markdown format and structure provided in the instructions with ALL headings and subheadings including the number of hashes '#' (like ## Information Extraction).
"""

def template(title:str, content:str, story_so_far: str = None, prev_chap_context: str = None) -> str:
    """Generate a prompt for the read chapter agent.

    Args:
        title (str): title of the chapter
        content (str): content of the chapter
        story_so_far (str, optional): summary of the story so far. Defaults to None. 
        prev_chap_context (str, optional): context of the previous chapter. Defaults to None.

    Returns:
        str: full prompt for the read chapter agent
    """
    #
    prompt = f"""# Task
{task()}"""
    #
    if story_so_far is not None:
      prompt+=f"""
# Story So Far:
{story_so_far}
"""
    if prev_chap_context is not None:
        prompt+=f"""
# Previous Chapter(s) Context:
{prev_chap_context}
"""
    #
    prompt+=f"""# Chapter Context:
## Chapter Title: {title}
## Chapter Content: 
---
{content}
---

# Instructions
---
{instructions(prev_chap_context)}
---
# General Reminders
{general_reminders()}"""
    #
    return prompt


class ReadChapterExtraction(BaseModel):
    characters: str
    events: str
    locations: str
    organizations: str
    things: str
    concepts: str
    main_arc: str

class ReadChapterResponse(BaseModel):
    full_response: str
    skipped_info_extraction: bool
    info_extraction: Optional[ReadChapterExtraction] = None
    chapter_summary: str

    def parse_response(response:str) -> "ReadChapterResponse":
        """Parse the response from the read chapter agent into the response model.

        Args:
            response (str): response from the read chapter agent

        Returns:
            ReadChapterResponse: parsed response model
        """
        full_response = response

        skipped_info_extraction = "<SKIPPED-EXTRACTION>" in response

        split1 = response.split("## General Chapter Summary")
        chapter_summary="## Chapter Summary"+split1[1]

        if skipped_info_extraction:
            info_extraction = None
        else:
            split2 = split1[0].split("## Information Extraction")
            text_extraction=split2[1].strip()

            extract_split = text_extraction.split("###")
            characters = "###"+extract_split[1]
            events = "###"+extract_split[2]
            locations = "###"+extract_split[3]
            organizations = "###"+extract_split[4]
            things = "###"+extract_split[5]
            concepts = "###"+extract_split[6]
            main_arc = "###"+extract_split[7]
            info_extraction = ReadChapterExtraction(characters=characters, 
                                  events=events, 
                                  locations=locations, 
                                  organizations=organizations, 
                                  things=things, 
                                  concepts=concepts,
                                  main_arc=main_arc)
        return ReadChapterResponse(full_response=full_response, skipped_info_extraction=skipped_info_extraction, info_extraction=info_extraction, chapter_summary=chapter_summary)

class ReadChapterAgent(BaseAgent):
    """Agent class for generating a single chapter summary and information extraction tasks."""
    def __init__(self, llm: LLMWrapper, client: QdrantClient):
        super().__init__(llm)
        self.client = client
    
    def mock_template(self) -> str:
        """Generate a mock template for the single chapter agent."""
        return template(r"{{title}}", r"{{content}}", r"<OPT>{{story_so_far}}</OPT>", r"<OPT>{{prev_chap_context}}</OPT>")
    
    def prompt(self, title:str, content:str, story_so_far: str = None, prev_chap_context: str = None) -> str:
        """Generate a prompt for the single chapter agent.
        
        Args:
            title (str): title of the chapter
            content (str): content of the chapter
            story_so_far (str, optional): summary of the story so far. Defaults to None.
            prev_chap_context (str, optional): context of the previous chapter. Defaults to None.
        
        Returns:
            str: full prompt for the single chapter agent
        """
        return template(title, content, story_so_far, prev_chap_context)
    
    def estimate_response_tokens(self, title:str, content:str, story_so_far: str = None, prev_chap_context: str = None) -> int:
        return super().estimate_response_tokens(self.prompt(title, content, story_so_far, prev_chap_context))
    
    def response_fields(self) -> dict:
        return ReadChapterResponse.model_fields
    
    def _store_response(self, response: ReadChapterResponse):
        """Store the response in the Qdrant database.
        
        Args:
            prompt (str): prompt used to generate the response
            response (str): response generated by the agent
        """
        payload = {
            "prompt": response.full_response,
            "response": response.dict()
        }
    
    def generate(self, title:str, content:str, story_so_far: str = None, prev_chap_context: str = None) -> ReadChapterResponse:
        """Generate a response for the single chapter agent.
        
        Args:
            title (str): title of the chapter
            content (str): content of the chapter
            story_so_far (str, optional): summary of the story so far. Defaults to None.
            prev_chap_context (str, optional): context of the previous chapter. Defaults to None.
        
        Returns:
            str: response generated by the single chapter agent
        """
        prompt = self.prompt(title, content, story_so_far, prev_chap_context)
        resp_str = super().generate(prompt)
        self.last_response: ReadChapterResponse = ReadChapterResponse.parse_response(resp_str)
        return self.last_response
    
    def _mock_generate(self, response:str, title:str, content:str, story_so_far: str = None, prev_chap_context: str = None) -> ReadChapterResponse:
        """Add the response to the agent history without actually calling the LLM. Used for testing.
        
        Args:
            response (str): response to add to the agent history
            title (str): title of the chapter
            content (str): content of the chapter
            story_so_far (str, optional): summary of the story so far. Defaults to None.
            prev_chap_context (str, optional): context of the previous chapter. Defaults to None.
            
        Returns:
            ReadChapterResponse: parsed response model
        """
        prompt = self.prompt(title, content, story_so_far, prev_chap_context)
        super()._mock_generate(prompt, response)
        self.last_response: ReadChapterResponse = ReadChapterResponse.parse_response(response)
        return self.last_response