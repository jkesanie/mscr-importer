from typing import Any, Union
import logging
from fair_mappings_schema import (
    MappingSpecification,
    MappingSpecificationTypeEnum,
    Agent,
    Person,
    Organization,
    Software
)

logger = logging.getLogger(__name__)


def transform(
    model: MappingSpecification,
    visibility: str = "PUBLIC",
    state: str = "DRAFT"
) -> dict[str, Any]:
    """
    Transform MappingSpecification to CrosswalkInfoDTO metadata.
    
    Args:
        model: Validated MappingSpecification instance
        visibility: Visibility setting (PUBLIC or PRIVATE)
        state: State setting (DRAFT, PUBLISHED, etc.)
        
    Returns:
        CrosswalkInfoDTO dict ready for API ingestion
    """
    logger.debug("INPUT: Transforming MappingSpecification: name=%s, type=%s, id=%s", 
                 model.name, model.type, model.id)
    logger.debug("INPUT: visibility=%s, state=%s", visibility, state)
    
    metadata = {
        "type": "CROSSWALK",
        "subType": _map_type_to_subtype(model.type) if model.type else "ANY",
        "visibility": visibility,
        "state": state,
        "label": {},
        "description": {},
        "versionLabel": None,
        "format": None,
        "sourceSchema": None,
        "targetSchema": None,
        "dctCreators": [],
        "dctContributors": [],
        "dctIdentifiers": [],
        "dctIssued": None,
        "dctLicense": None,
        "dctPublisher": None,
        "dctRelations": [],
        "dcatKeywords": [],
        "languages": ["en"]
    }
    
    if model.name:
        metadata["label"]["en"] = model.name
        logger.debug("Mapped name -> label[en]: %s", model.name)
    
    if model.description:
        metadata["description"]["en"] = model.description
        logger.debug("Mapped description -> description[en]: %s", model.description[:100])
    
    if model.version:
        metadata["versionLabel"] = model.version
        logger.debug("Mapped version -> versionLabel: %s", model.version)
    
    if model.type:
        metadata["format"] = _map_type_to_format(model.type)
        logger.debug("Mapped type -> format: %s", metadata["format"])
    
    if model.subject_source:
        metadata["sourceSchema"] = model.subject_source.id
        logger.debug("Mapped subject_source.id -> sourceSchema: %s", model.subject_source.id)
    
    if model.object_source:
        metadata["targetSchema"] = model.object_source.id
        logger.debug("Mapped object_source.id -> targetSchema: %s", model.object_source.id)
    
    if model.creator:
        creator_name = _extract_agent_name(model.creator)
        if creator_name:
            metadata["dctCreators"].append(creator_name)
            logger.debug("Mapped creator -> dctCreators: %s", creator_name)
    
    if model.author:
        author_name = _extract_agent_name(model.author)
        if author_name:
            metadata["dctContributors"].append(author_name)
            logger.debug("Mapped author -> dctContributors: %s", author_name)
    
    if model.id:
        metadata["dctIdentifiers"].append(model.id)
        logger.debug("Mapped id -> dctIdentifiers: %s", model.id)
    
    if model.publication_date:
        metadata["dctIssued"] = model.publication_date
        logger.debug("Mapped publication_date -> dctIssued: %s", model.publication_date)
    
    if model.license:
        metadata["dctLicense"] = model.license
        logger.debug("Mapped license -> dctLicense: %s", model.license)
    
    if model.documentation:
        metadata["dctRelations"].append(model.documentation)
        logger.debug("Mapped documentation -> dctRelations: %s", model.documentation)
    
    metadata = {k: v for k, v in metadata.items() if v is not None}
    
    logger.debug("OUTPUT: Transformed metadata: %s", metadata)
    return metadata


def _map_type_to_format(mapping_type: Union[MappingSpecificationTypeEnum, str]) -> str:
    """Map MappingSpecification type to MSCR format."""
    logger.debug("INPUT: _map_type_to_format called with: %s (type: %s)", mapping_type, type(mapping_type))
    mapping = {
        "sssom": "SSSOM",
        "r2rml": "MSCR",
        "rml": "MSCR",
        "sparql": "MSCR",
        "yarrrml": "MSCR",
        "xslt": "XSLT",
        "shacl": "MSCR",
        "other": "MSCR"
    }
    type_value = mapping_type.value if hasattr(mapping_type, 'value') else mapping_type
    result = mapping.get(type_value, "MSCR")
    logger.debug("OUTPUT: type %s -> format %s", type_value, result)
    return result


def _map_type_to_subtype(mapping_type: Union[MappingSpecificationTypeEnum, str]) -> str:
    """Map MappingSpecification type to MSCR subType."""
    logger.debug("INPUT: _map_type_to_subtype called with: %s (type: %s)", mapping_type, type(mapping_type))
    mapping = {
        "sssom": "SEMANTIC_MAPPING",
        "r2rml": "DATA_CROSSWALK",
        "rml": "DATA_CROSSWALK",
        "sparql": "SEMANTIC_ANNOTATION",
        "yarrrml": "DATA_CROSSWALK",
        "xslt": "DATA_CROSSWALK",
        "shacl": "SEMANTIC_ANNOTATION",
        "other": "ANY"
    }
    type_value = mapping_type.value if hasattr(mapping_type, 'value') else mapping_type
    result = mapping.get(type_value, "ANY")
    logger.debug("OUTPUT: type %s -> subType %s", type_value, result)
    return result


def _extract_agent_name(agent: Union[Agent, Person, Organization, Software]) -> str:
    """Extract name from Agent subclass."""
    logger.debug("INPUT: _extract_agent_name called with: name=%s, id=%s", agent.name, agent.id)
    if agent.name:
        logger.debug("OUTPUT: Returning agent.name: %s", agent.name)
        return agent.name
    if agent.id:
        logger.debug("OUTPUT: Returning agent.id: %s", agent.id)
        return agent.id
    logger.debug("OUTPUT: Returning empty string (no name or id)")
    return ""