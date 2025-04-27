from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query, Form
from typing import Optional, List
from app.domain.models.document import DocumentData
from app.infrastructure.document_sources.jira_source import JiraDocumentSource
from app.core.dependencies import get_vector_store_manager
from app.core.exceptions import ValidationException
import logging
import os
import json

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/import", response_model=dict)
async def import_jira_data(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    target_project: Optional[str] = Query(None, description="Optional Jira project key to filter issues (e.g., 'PROJ')"),
    vector_store_manager = Depends(get_vector_store_manager)
):
    """
    Import Jira data from a JSON file.
    
    Args:
        file: The Jira JSON file to import
        project_id: Optional project ID to associate with the documents
        conversation_id: Optional conversation ID to associate with the documents
        target_project: Optional Jira project key to filter issues
        vector_store_manager: Vector store manager dependency
        
    Returns:
        dict: A summary of the imported data
    """
    try:
        logger.info("Initializing Jira document source with vector store manager")
        
        # Initialize the Jira document source with the vector store manager
        jira_source = JiraDocumentSource(vector_store_manager=vector_store_manager)
        
        # Process the uploaded file and get the summary document
        document_data = await jira_source.process_upload(file)
        
        # Process the Jira data with optional project filter
        summary = await jira_source.processor.process_jira_data(
            data=document_data.content,
            file_name=file.filename,
            project_id=project_id,
            conversation_id=conversation_id,
            target_project=target_project
        )
        
        return {
            "message": "Jira data imported successfully",
            "summary": summary
        }
        
    except ValidationException as e:
        logger.error(f"Validation error during Jira import: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during Jira import: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error importing Jira data: {str(e)}")

@router.get("/projects", response_model=List[str])
async def list_available_projects(
    vector_store_manager = Depends(get_vector_store_manager)
):
    """
    List all available Jira projects in the data directory.
    
    Returns:
        List[str]: List of available project keys
    """
    try:
        # Get the data directory path
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        cleaned_data_dir = os.path.join(data_dir, "4.DataExtraction", "cleaned_data")
        
        # Get the latest timestamp directory
        timestamp_dirs = [d for d in os.listdir(cleaned_data_dir) if os.path.isdir(os.path.join(cleaned_data_dir, d))]
        if not timestamp_dirs:
            return []
        
        latest_dir = max(timestamp_dirs)
        latest_path = os.path.join(cleaned_data_dir, latest_dir)
        
        # Get all project files
        project_files = [f for f in os.listdir(latest_path) if f.endswith('.json') and f != 'extraction_summary.json']
        
        # Extract unique project keys
        project_keys = set()
        for file in project_files:
            # File format is PROJ_COLLECTION.json
            project_key = file.split('_')[0]
            project_keys.add(project_key)
        
        return sorted(list(project_keys))
        
    except Exception as e:
        logger.error(f"Error listing available projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing available projects: {str(e)}") 