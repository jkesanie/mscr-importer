from pathlib import Path
from typing import Union
import yaml
import requests
import logging
from pydantic import ValidationError

from fair_mappings_schema import MappingSpecification

logger = logging.getLogger(__name__)


class ValidatorError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_yaml_content(yaml_content: str) -> MappingSpecification:
    """
    Validate YAML content against the MappingSpecification schema.
    
    Args:
        yaml_content: String containing YAML content
        
    Returns:
        Validated MappingSpecification instance
        
    Raises:
        ValidatorError: If validation fails
    """
    logger.debug("INPUT: YAML content (first 500 chars): %s", yaml_content[:500])
    
    try:
        data = yaml.safe_load(yaml_content)
        logger.debug("OUTPUT: Parsed YAML data: %s", data)
    except yaml.YAMLError as e:
        logger.error("YAML parse error: %s", e)
        raise ValidatorError(f"Invalid YAML: {e}")
    
    if data is None:
        raise ValidatorError("YAML content is empty")
    
    try:
        model = MappingSpecification(**data)
        logger.debug("OUTPUT: Validated MappingSpecification: name=%s, type=%s, id=%s", 
                     model.name, model.type, model.id)
        return model
    except ValidationError as e:
        errors = _summarize_validation_errors(e)
        logger.error("Validation errors: %s", "\n".join(errors))
        raise ValidatorError(f"Validation failed:\n" + "\n".join(errors))


def validate_from_url(url: str, timeout: int = 30) -> MappingSpecification:
    """
    Download YAML from URL and validate against schema.
    
    Args:
        url: URL to download YAML from
        timeout: Request timeout in seconds
        
    Returns:
        Validated MappingSpecification instance
        
    Raises:
        ValidatorError: If download or validation fails
    """
    logger.debug("INPUT: Downloading YAML from URL: %s", url)
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        yaml_content = response.text
        logger.debug("OUTPUT: Downloaded %d bytes from URL", len(yaml_content))
    except requests.RequestException as e:
        logger.error("Failed to download from URL %s: %s", url, e)
        raise ValidatorError(f"Failed to download YAML from {url}: {e}")
    
    return validate_yaml_content(yaml_content)


def validate_from_file(file_path: Union[str, Path], timeout: int = 30) -> MappingSpecification:
    """
    Load YAML from file and validate against schema.
    
    Args:
        file_path: Path to YAML file
        timeout: Not used for file operations, kept for API consistency
        
    Returns:
        Validated MappingSpecification instance
        
    Raises:
        ValidatorError: If file read or validation fails
    """
    path = Path(file_path)
    logger.debug("INPUT: Loading YAML from file: %s", path)
    
    if not path.exists():
        logger.error("File not found: %s", path)
        raise ValidatorError(f"File not found: {file_path}")
    
    if not path.is_file():
        logger.error("Not a file: %s", path)
        raise ValidatorError(f"Not a file: {file_path}")
    
    try:
        with open(path, 'r') as f:
            yaml_content = f.read()
        logger.debug("OUTPUT: Read %d bytes from file", len(yaml_content))
    except IOError as e:
        logger.error("Failed to read file %s: %s", file_path, e)
        raise ValidatorError(f"Failed to read file {file_path}: {e}")
    
    return validate_yaml_content(yaml_content)


def validate_path_or_url(path_or_url: str, timeout: int = 30) -> MappingSpecification:
    """
    Auto-detect if input is a file path or URL and validate accordingly.
    
    Args:
        path_or_url: File path or URL to YAML
        timeout: Request timeout for URL downloads
        
    Returns:
        Validated MappingSpecification instance
        
    Raises:
        ValidatorError: If validation fails
    """
    logger.debug("INPUT: Validating path_or_url: %s", path_or_url)
    
    if path_or_url.startswith(('http://', 'https://')):
        logger.debug("Detected URL, calling validate_from_url")
        result = validate_from_url(path_or_url, timeout)
    else:
        logger.debug("Detected file path, calling validate_from_file")
        result = validate_from_file(path_or_url, timeout)
    
    logger.debug("OUTPUT: Validation complete, returning MappingSpecification")
    return result


def _summarize_validation_errors(error: ValidationError) -> list[str]:
    """
    Summarize Pydantic validation errors in a readable format.
    
    Args:
        error: Pydantic ValidationError instance
        
    Returns:
        List of summarized error messages
    """
    summarized = []
    for err in error.errors():
        field = ".".join(str(loc) for loc in err['loc'])
        msg = err['msg']
        summarized.append(f"  {field}: {msg}")
    return summarized