from fastapi import APIRouter, Depends, Query, HTTPException, File, UploadFile, Form
from typing import List, Optional, Dict, Any
import os
import json

from app.application.services.document_service import DocumentService
from app.api.container import get_document_service
from app.core.exceptions import NotFoundException, ValidationException
from app.infrastructure.database.session import get_db
from json import JSONDecodeError
from sqlalchemy.orm import Session


router = APIRouter(prefix="/jira", tags=["Jira"])

@router.get(
    "/files",
    response_model=List[Dict[str, Any]],
    summary="List Available Jira Projects",
    description="List all available Jira project_keys and their associated JSON files in the data directory"
)
async def list_jira_projects(
    timestamp: str = Query("latest", description="Timestamp of the data directory (use 'latest' for the most recent)"),
    service: DocumentService = Depends(get_document_service)
):
    """
    List all available Jira project_keys and their associated JSON files in the data directory.
    """
    jira_source = service.document_sources.get("jira")
    if not jira_source:
        raise ValidationException("Jira document source not available")
    data_dir = jira_source.data_dir
    if timestamp == "latest":
        try:
            timestamp = jira_source._get_latest_timestamp()
        except Exception as e:
            raise ValidationException(f"Error getting latest timestamp: {str(e)}")
    dir_path = os.path.join(data_dir, timestamp)
    if not os.path.exists(dir_path):
        raise ValidationException(f"Data directory not found: {dir_path}")
    # Map project_key to list of files
    project_files = {}
    for file_name in os.listdir(dir_path):
        if file_name.endswith('.json') and file_name != 'extraction_summary.json':
            file_path = os.path.join(dir_path, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                    if isinstance(docs, dict):
                        docs = [docs]
                    for doc in docs:
                        key = doc.get("key", "")
                        project_key = key.split("-")[0] if "-" in key else "UNKNOWN"
                        if project_key not in project_files:
                            project_files[project_key] = set()
                        project_files[project_key].add(file_name)
            except Exception:
                continue
    # Format output
    result = []
    for project_key, files in project_files.items():
        result.append({
            "project_key": project_key,
            "files": sorted(list(files))
        })
    return result

@router.post(
    "/import",
    response_model=Dict[str, Any],
    summary="Import Jira Project Data",
    description="Import Jira data for a given project_key from all relevant JSON files in the data directory"
)
async def import_jira_project(
    project_key: str = Query(..., description="Project key to import (e.g., 'AL')"),
    timestamp: str = Query("latest", description="Timestamp of the data directory (use 'latest' for the most recent)"),
    project_id: Optional[str] = Query(None, description="Project ID to associate the document with"),
    conversation_id: Optional[str] = Query(None, description="Conversation ID to associate the document with"),
    service: DocumentService = Depends(get_document_service),
    db: Session = Depends(get_db)
):
    """
    Import Jira data for a given project_key from all relevant JSON files in the data directory.
    This includes both issue files and summary files if they exist.
    """
    jira_source = service.document_sources.get("jira")
    if not jira_source:
        raise ValidationException("Jira document source not available")
    if timestamp == "latest":
        timestamp = jira_source._get_latest_timestamp()
    dir_path = os.path.join(jira_source.data_dir, timestamp)
    if not os.path.exists(dir_path):
        raise ValidationException(f"Data directory not found: {dir_path}")
    
    # Find all files containing issues for the given project_key
    input_files = []
    summary_files = []
    
    for file_name in os.listdir(dir_path):
        if file_name.endswith('.json') and file_name != 'extraction_summary.json':
            file_path = os.path.join(dir_path, file_name)
            
            # Check if this is a summary file for the project
            if file_name.endswith('_SUMMARY.json') and file_name.startswith(f"{project_key}_"):
                summary_files.append(file_path)
                continue
                
            # Check if this is an issue file for the project
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    docs = json.load(f)
                    if isinstance(docs, dict):
                        docs = [docs]
                    for doc in docs:
                        key = doc.get("key", "")
                        if key.startswith(f"{project_key}-"):
                            input_files.append(file_path)
                            break
            except Exception:
                continue
    
    # Process summary file if it exists
    summary_result = None
    if summary_files:
        try:
            # For now, just load the first summary file (could be more robust)
            with open(summary_files[0], 'r', encoding='utf-8') as f:
                summary_docs = json.load(f)
                # Process the summary data
                summary_result = await jira_source.processor.process_jira_data(
                    data=summary_docs,
                    file_name=os.path.basename(summary_files[0]),
                    project_id=project_id,
                    conversation_id=conversation_id,
                    db_session=db,
                    target_project=project_key,
                    is_summary=True  # Flag to indicate this is a summary file
                )
        except Exception as e:
            # Log the error but continue with issue processing
            logger.error(f"Error processing summary file: {str(e)}")
    
    # Process issue files if they exist
    issues_result = None
    if input_files:
        # Aggregate all issues for the project_key
        all_issues = []
        for file_path in input_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                docs = json.load(f)
                if isinstance(docs, dict):
                    docs = [docs]
                for doc in docs:
                    key = doc.get("key", "")
                    if key.startswith(f"{project_key}-"):
                        all_issues.append(doc)
        
        if all_issues:
            # Process the Jira data
            issues_result = await jira_source.processor.process_jira_data(
                data=all_issues,
                file_name=f"{project_key}_ALL.json",
                project_id=project_id,
                conversation_id=conversation_id,
                db_session=db,
                target_project=project_key,
                is_summary=False  # Flag to indicate this is not a summary file
            )
    
    # Return appropriate response based on what was processed
    if summary_result and issues_result:
        return {
            "message": "Jira project and summary imported successfully",
            "summary": summary_result,
            "issues": issues_result
        }
    elif summary_result:
        return {
            "message": "Jira project summary imported successfully",
            "summary": summary_result
        }
    elif issues_result:
        return {
            "message": "Jira project issues imported successfully",
            "issues": issues_result
        }
    else:
        raise ValidationException(f"No issues or summary found for project_key {project_key}")

@router.delete(
    "/clean",
    response_model=Dict[str, Any],
    summary="Clean Jira Data",
    description="Delete Jira data for a specific project or file"
)
async def clean_jira_data(
    project_name: Optional[str] = Query(None, description="Name of the Jira project"),
    file_name: Optional[str] = Query(None, description="Name of the specific file to delete"),
    timestamp: Optional[str] = Query(None, description="Timestamp to delete data from"),
    document_service: DocumentService = Depends(get_document_service)
):
    """
    Delete Jira data for a specific project or file.
    
    Args:
        project_name: Optional name of the Jira project. If not provided, will be extracted from file_name
        file_name: Optional name of the specific file to delete
        timestamp: Optional timestamp to delete data from a specific time
        
    Returns:
        Dict containing the number of documents deleted
    """
    try:
        # If project_name is not provided, extract it from file_name
        if not project_name and file_name:
            project_name = os.path.splitext(file_name)[0]
        elif not project_name:
            raise HTTPException(
                status_code=400,
                detail="Either project_name or file_name must be provided"
            )
            
        # Construct source ID based on parameters
        source_id = f"jira_{project_name}"
        if file_name:
            source_id = f"{source_id}_{file_name}"
        if timestamp:
            source_id = f"{source_id}_{timestamp}"
            
        # Get all documents with this source ID
        documents = await document_service.repository.get_all_by_source("jira", source_id)
        
        if not documents:
            raise HTTPException(
                status_code=404,
                detail=f"No Jira documents found for project {project_name}"
            )
            
        # Delete each document
        deleted_count = 0
        for doc in documents:
            await document_service.delete_document(doc.id)
            deleted_count += 1
            
        return {
            "message": f"Successfully deleted {deleted_count} Jira documents",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error cleaning Jira data: {str(e)}"
        ) 