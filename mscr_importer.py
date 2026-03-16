import logging
import typer
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from validator import validate_path_or_url, ValidatorError
from transformer import transform
from api_client import ingest_crosswalk, APIError

load_dotenv()
logging.basicConfig(level=logging.ERROR)

app = typer.Typer(help="CLI for harvesting YAML data and ingesting to MSCR API")
console = Console()


def process_content_url(content_url: Optional[str]) -> tuple[Optional[str], Optional[Path]]:
    """
    Process content_url to determine API parameters.
    
    Args:
        content_url: The content_url value from MappingSpecification
        
    Returns:
        Tuple of (content_url_for_api, file_path_for_upload)
        - http(s):// → (content_url, None)
        - file:// → (None, Path(local_path))
        - None → (None, None)
    """
    logger = logging.getLogger(__name__)
    logger.debug("INPUT: process_content_url called with: %s", content_url)
    
    if not content_url:
        logger.debug("OUTPUT: No content_url, returning (None, None)")
        return None, None
    
    if content_url.startswith("http://") or content_url.startswith("https://"):
        logger.debug("OUTPUT: HTTP URL detected, returning (content_url=%s, None)", content_url)
        return content_url, None
    
    elif content_url.startswith("file://"):
        local_path = content_url[7:]
        logger.debug("OUTPUT: File URL detected, returning (None, Path(%s))", local_path)
        return None, Path(local_path)
    
    else:
        logger.debug("OUTPUT: Unknown URL scheme, treating as content_url: %s", content_url)
        return content_url, None


def process_and_ingest(
    path_or_url: str,
    api_base_url: str,
    api_key: str,
    target: Optional[str] = None,
    visibility: str = "PUBLIC",
    state: str = "DRAFT",
    dry_run: bool = False,
    verbose: bool = False,
    timeout: int = 120
) -> None:
    """
    Process YAML (validate, transform) and ingest to MSCR API.
    
    Args:
        path_or_url: File path or URL to YAML
        api_base_url: MSCR API base URL
        api_key: JWT API key for authentication
        target: Target identifier
        visibility: Visibility setting (PUBLIC or PRIVATE)
        state: State setting (DRAFT, PUBLISHED, etc.)
        dry_run: If True, skip ingestion
        verbose: If True, print detailed output
        timeout: Request timeout in seconds
    """
    logger = logging.getLogger(__name__)
    logger.warning("INPUT: process_and_ingest called")
    logger.warning("INPUT: path_or_url=%s", path_or_url)
    logger.warning("INPUT: api_base_url=%s", api_base_url)
    logger.warning("INPUT: target=%s", target)
    logger.warning("INPUT: visibility=%s", visibility)
    logger.warning("INPUT: state=%s", state)
    logger.warning("INPUT: dry_run=%s", dry_run)
    logger.warning("INPUT: verbose=%s", verbose)
    logger.warning("INPUT: timeout=%s", timeout)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Validating...", total=None)
        
        try:
            logger.debug("STEP: Starting validation")
            model = validate_path_or_url(path_or_url, timeout)
            progress.update(task, description="[green]✓ Validation complete")
            logger.debug("STEP: Validation complete, model.name=%s", model.name)
            
            if verbose:
                console.print(f"[dim]Validated MappingSpecification: {model.name or 'unnamed'}[/dim]")
                
        except ValidatorError as e:
            logger.error("Validation failed: %s", e)
            console.print(f"[red]FAILURE: {e}")
            raise typer.Exit(1)
        
        task = progress.add_task("Transforming...", total=None)
        logger.debug("STEP: Starting transformation")
        metadata = transform(model, visibility=visibility, state=state)
        progress.update(task, description="[green]✓ Transformation complete")
        logger.debug("STEP: Transformation complete")
        
        if verbose:
            console.print(f"[dim]Metadata: {metadata}[/dim]")
        
        content_url = model.content_url
        logger.debug("STEP: Processing content_url=%s", content_url)
        content_url_for_api, file_path_for_upload = process_content_url(content_url)
        logger.debug("STEP: content_url_for_api=%s, file_path_for_upload=%s", content_url_for_api, file_path_for_upload)
        
        if verbose and content_url_for_api:
            console.print(f"[dim]Content URL: {content_url_for_api}[/dim]")
        if verbose and file_path_for_upload:
            console.print(f"[dim]File upload: {file_path_for_upload}[/dim]")
        
        if dry_run:
            logger.debug("STEP: Dry run mode, skipping ingestion")
            console.print("[yellow]Dry run - skipping ingestion")
            console.print("SUCCESS")
            return
        
        task = progress.add_task("Ingesting to API...", total=None)
        logger.debug("STEP: Starting API ingestion")
        
        try:
            result = ingest_crosswalk(
                metadata=metadata,
                api_base_url=api_base_url,
                api_key=api_key,
                content_url=content_url_for_api,
                target=target,
                file_path=file_path_for_upload,
                timeout=timeout
            )
            progress.update(task, description="[green]✓ Ingestion complete")
            logger.debug("STEP: Ingestion complete")
            
            if verbose:
                console.print(f"[dim]API response: {result}[/dim]")
            
            console.print("SUCCESS")
            logger.debug("OUTPUT: Process completed successfully")
            
        except APIError as e:
            logger.error("API ingestion failed: %s", e)
            console.print(f"[red]FAILURE: {e}")
            raise typer.Exit(1)


@app.command()
def harvest(
    url: str = typer.Argument(..., help="URL to download YAML from"),
    api_base_url: str = typer.Option(
        "https://mscr-release.2.rahtiapp.fi/datamodel-api",
        "--api",
        "-a",
        envvar="MSCR_API_URL",
        help="MSCR API base URL"
    ),
    api_key: str = typer.Option(
        None,
        "--key",
        "-k",
        envvar="MSCR_API_KEY",
        help="JWT API key for authentication"
    ),
    target: str = typer.Option(
        None,
        "--target",
        help="Target identifier"
    ),
    visibility: str = typer.Option(
        "PUBLIC",
        "--visibility",
        help="Visibility: PUBLIC or PRIVATE"
    ),
    state: str = typer.Option(
        "DRAFT",
        "--state",
        help="State: DRAFT, PUBLISHED, INVALID, DEPRECATED, REMOVED"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, skip ingestion"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    timeout: int = typer.Option(120, "--timeout", help="Request timeout in seconds")
):
    """Download YAML from URL, validate, transform, and ingest to MSCR API."""
    logger = logging.getLogger(__name__)
    logger.warning("COMMAND: harvest called with url=%s", url)
    logger.warning("COMMAND: api_base_url=%s, target=%s", api_base_url, target)
    logger.warning("COMMAND: visibility=%s, state=%s, dry_run=%s", visibility, state, dry_run)
    
    if not api_key and not dry_run:
        console.print("[red]FAILURE: API key required (--key or MSCR_API_KEY env var)")
        raise typer.Exit(1)
    
    process_and_ingest(
        path_or_url=url,
        api_base_url=api_base_url,
        api_key=api_key,
        target=target,
        visibility=visibility,
        state=state,
        dry_run=dry_run,
        verbose=verbose,
        timeout=timeout
    )


@app.command()
def ingest(
    file: str = typer.Argument(..., help="Local YAML file to ingest"),
    api_base_url: str = typer.Option(
        "https://mscr-release.2.rahtiapp.fi/datamodel-api",
        "--api",
        "-a",
        envvar="MSCR_API_URL",
        help="MSCR API base URL"
    ),
    api_key: str = typer.Option(
        None,
        "--key",
        "-k",
        envvar="MSCR_API_KEY",
        help="JWT API key for authentication"
    ),
    target: str = typer.Option(
        None,
        "--target",
        help="Target identifier"
    ),
    visibility: str = typer.Option(
        "PUBLIC",
        "--visibility",
        help="Visibility: PUBLIC or PRIVATE"
    ),
    state: str = typer.Option(
        "DRAFT",
        "--state",
        help="State: DRAFT, PUBLISHED, INVALID, DEPRECATED, REMOVED"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate only, skip ingestion"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    timeout: int = typer.Option(120, "--timeout", help="Request timeout in seconds")
):
    """Load local YAML file, validate, transform, and ingest to MSCR API."""
    logger = logging.getLogger(__name__)
    logger.warning("COMMAND: ingest called with file=%s", file)
    logger.warning("COMMAND: api_base_url=%s, target=%s", api_base_url, target)
    logger.warning("COMMAND: visibility=%s, state=%s, dry_run=%s", visibility, state, dry_run)
    
    if not api_key and not dry_run:
        console.print("[red]FAILURE: API key required (--key or MSCR_API_KEY env var)")
        raise typer.Exit(1)
    
    process_and_ingest(
        path_or_url=file,
        api_base_url=api_base_url,
        api_key=api_key,
        target=target,
        visibility=visibility,
        state=state,
        dry_run=dry_run,
        verbose=verbose,
        timeout=timeout
    )


@app.command()
def validate(
    path_or_url: str = typer.Argument(..., help="File path or URL to YAML"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    timeout: int = typer.Option(60, "--timeout", help="Request timeout in seconds")
):
    """Validate YAML against the MappingSpecification schema."""
    logger = logging.getLogger(__name__)
    logger.debug("COMMAND: validate called with path_or_url=%s", path_or_url)
    
    try:
        model = validate_path_or_url(path_or_url, timeout)
        
        if verbose:
            console.print(f"[dim]Name: {model.name or 'unnamed'}[/dim]")
            type_value = model.type.value if hasattr(model.type, 'value') else model.type
            console.print(f"[dim]Type: {type_value if model.type else 'not specified'}[/dim]")
            console.print(f"[dim]ID: {model.id or 'not specified'}[/dim]")
        
        console.print("SUCCESS")
        logger.debug("OUTPUT: Validation successful")
        
    except ValidatorError as e:
        logger.error("Validation failed: %s", e)
        console.print(f"[red]FAILURE: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()