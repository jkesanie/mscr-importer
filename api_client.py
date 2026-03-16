import json
import requests
import logging
from pathlib import Path
from typing import Any, Optional
from requests_toolbelt.multipart.encoder import MultipartEncoder

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom exception for API errors."""
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


def ingest_crosswalk(
    metadata: dict[str, Any],
    api_base_url: str,
    api_key: str,
    content_url: Optional[str] = None,
    target: Optional[str] = None,
    file_path: Optional[Path] = None,
    timeout: int = 120
) -> dict[str, Any]:
    """
    Ingest crosswalk to MSCR API via PUT /v2/crosswalkFull.
    
    Args:
        metadata: CrosswalkInfoDTO metadata dict
        api_base_url: Base URL (e.g., https://mscr-release.2.rahtiapp.fi/datamodel-api)
        api_key: JWT bearer token
        content_url: URL to content (for http:// URLs)
        target: Target identifier
        file_path: Path to file for upload (for file:// URLs)
        timeout: Request timeout in seconds
        
    Returns:
        API response as dictionary
        
    Raises:
        APIError: If API request fails or returns non-2xx status
    """
    logger.debug("INPUT: ingest_crosswalk called")
    logger.debug("INPUT: api_base_url=%s", api_base_url)
    logger.debug("INPUT: content_url=%s", content_url)
    logger.debug("INPUT: target=%s", target)
    logger.debug("INPUT: file_path=%s", file_path)
    logger.debug("INPUT: metadata=%s", metadata)
    
    endpoint = f"{api_base_url}/v2/frontend/crosswalkFull"
    logger.debug("OUTPUT: API endpoint: %s", endpoint)
    
    metadata_json = json.dumps(metadata)
    logger.debug("OUTPUT: metadata JSON (%d bytes): %s", len(metadata_json), metadata_json[:500])
    
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    logger.debug("OUTPUT: Request headers: %s", headers)
    
    try:
        # Build multipart form data
        encoder_fields = {
            "metadata": metadata_json
        }
        
        if content_url:
            encoder_fields["contentURL"] = content_url
        
        if target:
            encoder_fields["target"] = target
        
        if file_path:
            file_path = Path(file_path)
            logger.debug("OUTPUT: File upload mode detected, path=%s", file_path)
            if not file_path.exists():
                logger.error("File not found: %s", file_path)
                raise APIError(f"File not found: {file_path}")
            
            # Read file content into memory (Option 2)
            with open(file_path, 'rb') as f:
                file_content = f.read()
            logger.debug("OUTPUT: File loaded into memory, size=%d bytes", len(file_content))
            
            # Add file content to multipart fields
            encoder_fields["file"] = ("file", file_content, "application/octet-stream")
            logger.debug("OUTPUT: File content added to multipart request")
        else:
            logger.debug("OUTPUT: HTTP URL mode - no file upload")
        
        # Create MultipartEncoder to ensure multipart/form-data encoding
        encoder = MultipartEncoder(fields=encoder_fields)
        logger.debug("OUTPUT: MultipartEncoder created, content-type: %s", encoder.content_type)
        
        # Log payload fields (without file content for large files)
        logger.debug("OUTPUT: Payload fields: %s", list(encoder_fields.keys()))
        for key, value in encoder_fields.items():
            if key == "file":
                # Value is a tuple (filename, content, mime_type)
                _, content, mime_type = value
                logger.debug("OUTPUT:   %s: file (%d bytes, %s)", key, len(content), mime_type)
            else:
                # Truncate long values
                value_str = str(value)[:200] + ("..." if len(str(value)) > 200 else "")
                logger.debug("OUTPUT:   %s: %s", key, value_str)
        
        # Add Content-Type header from encoder
        headers["Content-Type"] = encoder.content_type
        
        logger.debug("OUTPUT: Sending PUT request with multipart/form-data to %s", endpoint)
        response = requests.put(
            endpoint,
            data=encoder,
            headers=headers,
            timeout=timeout
        )
        
        logger.debug("OUTPUT: API response status: %s", response.status_code)
        response.raise_for_status()
        result = response.json()
        logger.debug("OUTPUT: API response JSON: %s", result)
        return result
        
    except requests.HTTPError as e:
        status = e.response.status_code if e.response else None
        body = e.response.text if e.response else str(e)
        logger.error("HTTP error: status=%s, body=%s", status, body)
        raise APIError(f"API error: {status} {body}", status_code=status)
    except requests.RequestException as e:
        logger.error("Network error: %s", e)
        raise APIError(f"Network error: {e}")