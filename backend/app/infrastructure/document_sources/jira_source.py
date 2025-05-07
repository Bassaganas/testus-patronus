from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path
from fastapi import UploadFile
from app.infrastructure.document_sources.base import DocumentSource
from app.core.exceptions import ValidationException
import logging
from datetime import datetime
from app.infrastructure.repositories.document_repository import DocumentRepository
from app.domain.schemas.document import DocumentCreate

from app.domain.models.document import ContentPart, DocumentData

logger = logging.getLogger(__name__)

class JiraProcessor:
    """
    Dedicated processor for Jira data that's optimized for issue-specific content.
    """
    
    def __init__(self, vector_store_manager):
        self.vector_store = vector_store_manager
        logger.info("JiraProcessor initialized")
    
    def _get_project_key(self, issue: Dict[str, Any]) -> str:
        """Extract project key from an issue."""
        # First try to get from fields.project.key
        project = issue.get('fields', {}).get('project', {})
        project_key = project.get('key')
        
        # If not found, try to extract from issue key (e.g., "PROJ-123" -> "PROJ")
        if not project_key and 'key' in issue:
            key_parts = issue['key'].split('-')
            if len(key_parts) > 1:
                project_key = key_parts[0]
        
        return project_key or 'UNKNOWN'
    
    def _group_issues_by_project(self, data: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group Jira issues by project.
        
        Args:
            data: List of Jira issues
            
        Returns:
            Dict[str, List[Dict[str, Any]]]: Issues grouped by project key
        """
        projects = {}
        for issue in data:
            project_key = self._get_project_key(issue)
            if project_key not in projects:
                projects[project_key] = []
            projects[project_key].append(issue)
        return projects
    
    async def process_jira_data(self, data: List[Dict[str, Any]], file_name: str, db_session, project_id: Optional[str] = None, 
                              conversation_id: Optional[str] = None, target_project: Optional[str] = None, is_summary: bool = False, single_document: Optional[bool] = False, chunk_size: Optional[int] = 400) -> str:
        """
        Process Jira data and store each issue as a separate document in the vector store.
        
        Args:
            data: List of Jira issues or a JSON string containing the issues
            file_name: Name of the file
            db_session: Database session
            project_id: Optional project ID to associate with the documents
            conversation_id: Optional conversation ID to associate with the documents
            target_project: Optional project key to filter issues
            is_summary: Flag indicating if this is a summary file (True) or issue file (False)
            
        Returns:
            str: A summary of the processed data
        """
        try:
            # Handle string input by parsing it as JSON
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    raise ValidationException("Invalid JSON data")
            
            # Ensure data is a list
            if not isinstance(data, list):
                logger.warning(f"Expected list but got {type(data)}. Converting to list.")
                data = [data]
            
            # If this is a summary file, process it differently
            if is_summary:
                logger.info(f"Processing summary file: {file_name}")
                return await self._process_summary_data(data, file_name, db_session, project_id, conversation_id, target_project)
            
            # Group issues by project
            projects = self._group_issues_by_project(data)
            
            # If target project is specified, filter to just that project
            if target_project:
                if target_project not in projects:
                    # Try to find a project that matches the target project as a substring
                    matching_projects = [k for k in projects.keys() if target_project in k]
                    if matching_projects:
                        # Use the first matching project
                        target_project = matching_projects[0]
                        logger.info(f"Using matching project: {target_project}")
                    else:
                        raise ValidationException(f"Project {target_project} not found in the data")
                projects = {target_project: projects[target_project]}
            
            # Process each project
            project_summaries = []
            for project_key, issues in projects.items():
                logger.info(f"Processing project {project_key} with {len(issues)} issues")
                
                # Initialize counters for this project
                issue_count = 0
                status_counts = {}
                priority_counts = {}
                
                # Process each issue in the project
                for issue in issues:
                    fields = issue.get('fields', {})
                    key = issue.get('key', '')
                    if not key:
                        continue
                    
                    # Extract issue data
                    summary = fields.get('summary', '')
                    description = fields.get('description', '')
                    status = fields.get('status', {}).get('name', 'Unknown')
                    priority = fields.get('priority', {}).get('name', 'Unknown')
                    issue_type = fields.get('issuetype', {}).get('name', 'Unknown')
                    created = fields.get('created', '')
                    updated = fields.get('updated', '')
                    resolution_date = fields.get('resolutiondate', '')
                    
                    # Extract assignee and reporter
                    assignee = fields.get('assignee', {}).get('displayName', 'Unassigned')
                    reporter = fields.get('reporter', {}).get('displayName', 'Unknown')
                    
                    # Extract components and labels
                    components = [comp.get('name', '') for comp in fields.get('components', [])]
                    labels = fields.get('labels', [])
                    
                    # Extract comments
                    comments = fields.get('comment', {}).get('comments', [])
                    comment_texts = []
                    for comment in comments:
                        author = comment.get('author', {}).get('displayName', 'Unknown')
                        body = comment.get('body', '')
                        created = comment.get('created', '')
                        comment_texts.append(f"Comment by {author} on {created}:\n{body}\n")
                    
                    # Create a comprehensive text representation of the issue
                    issue_text = f"""
Issue: {key}
Type: {issue_type}
Status: {status}
Priority: {priority}
Summary: {summary}

Description:
{description}

Components: {', '.join(components) if components else 'None'}
Labels: {', '.join(labels) if labels else 'None'}

Assignee: {assignee}
Reporter: {reporter}

Created: {created}
Updated: {updated}
Resolution Date: {resolution_date}

Comments:
{'-' * 40}
{chr(10).join(comment_texts) if comment_texts else 'No comments'}
{'-' * 40}
"""
                    # Create metadata for this issue
                    issue_metadata = {
                        'document_id': f"{project_key}_{key}",
                        'issue_key': key,
                        'issue_type': issue_type,
                        'status': status,
                        'priority': priority,
                        'project_key': project_key,
                        'source_type': 'jira',
                        'file_name': file_name
                    }
                    
                    # Add project and conversation IDs if provided
                    if project_id:
                        issue_metadata['project_id'] = project_id
                    if conversation_id:
                        issue_metadata['conversation_id'] = conversation_id
                    
                    # Add to vector store
                    await self.vector_store.add_documents(
                        [{"page_content": issue_text, "metadata": issue_metadata}],
                        document_id=f"{project_key}_{key}",
                        project_id=project_id,
                        conversation_id=conversation_id
                    )
                    
                    # Update counters
                    issue_count += 1
                    status_counts[status] = status_counts.get(status, 0) + 1
                    priority_counts[priority] = priority_counts.get(priority, 0) + 1
                    
                    # Create document record in backend DB
                    document_create = DocumentCreate(
                        title=summary,
                        source_type="jira",
                        source_id=f"{project_key}_{key}",
                        file_name=file_name,
                        file_type="jira_issue",
                        file_size=len(issue_text.encode("utf-8")),
                        content=issue_text,
                        doc_metadata=issue_metadata,
                        project_id=project_id,
                        conversation_id=conversation_id
                    )
                    repo = DocumentRepository(db_session)
                    await repo.create(document_create)
                
                # Create a summary for this project
                project_summary = f"""
Project: {project_key}
Total Issues: {issue_count}

Status Distribution:
"""
                for status, count in status_counts.items():
                    project_summary += f"- {status}: {count}\n"
                
                project_summary += "\nPriority Distribution:\n"
                for priority, count in priority_counts.items():
                    project_summary += f"- {priority}: {count}\n"
                
                project_summaries.append(project_summary)
            
            # Combine all project summaries
            return "\n\n".join(project_summaries)
            
        except Exception as e:
            logger.error(f"Error processing Jira data: {str(e)}")
            raise
    
    async def _process_summary_data(self, data: List[Dict[str, Any]], file_name: str, db_session, project_id: Optional[str] = None, 
                                  conversation_id: Optional[str] = None, target_project: Optional[str] = None) -> str:
        """
        Process Jira summary data and store it as a document in the vector store.
        
        Args:
            data: List of Jira summary dictionaries
            file_name: Name of the file
            db_session: Database session
            project_id: Optional project ID to associate with the documents
            conversation_id: Optional conversation ID to associate with the documents
            target_project: Optional project key to filter summaries
            
        Returns:
            str: A summary of the processed data
        """
        try:
            # Process each summary document
            for summary_doc in data:
                fields = summary_doc.get('fields', {})
                key = summary_doc.get('key', '')
                
                # Extract project key from the key (e.g., "REST-SUMMARY" -> "REST")
                project_key = key.split('-')[0] if '-' in key else key
                
                # If target project is specified, filter to just that project
                if target_project and project_key != target_project:
                    continue
                
                # Extract summary data
                summary_text = fields.get('summary', '')
                contributors = fields.get('contributors', [])
                assignees = fields.get('assignees', [])
                reporters = fields.get('reporters', [])
                components = fields.get('components', [])
                issue_count = fields.get('issue_count', 0)
                
                # Create a comprehensive text representation of the summary
                summary_content = f"""
Project Summary: {project_key}
Total Issues: {issue_count}

Summary:
{summary_text}

Contributors: {', '.join(contributors) if contributors else 'None'}
Assignees: {', '.join(assignees) if assignees else 'None'}
Reporters: {', '.join(reporters) if reporters else 'None'}
Components: {', '.join(components) if components else 'None'}
"""
                
                # Create metadata for this summary
                summary_metadata = {
                    'document_id': f"{project_key}_SUMMARY",
                    'project_key': project_key,
                    'source_type': 'jira',
                    'file_name': file_name,
                    'document_type': 'project_summary'
                }
                
                # Add project and conversation IDs if provided
                if project_id:
                    summary_metadata['project_id'] = project_id
                if conversation_id:
                    summary_metadata['conversation_id'] = conversation_id
                
                # Add to vector store
                await self.vector_store.add_documents(
                    [{"page_content": summary_content, "metadata": summary_metadata}],
                    document_id=f"{project_key}_SUMMARY",
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                
                # Create document record in backend DB
                document_create = DocumentCreate(
                    title=f"Project Summary: {project_key}",
                    source_type="jira",
                    source_id=f"{project_key}_SUMMARY",
                    file_name=file_name,
                    file_type="jira_project_summary",
                    file_size=len(summary_content.encode("utf-8")),
                    content=summary_content,
                    doc_metadata=summary_metadata,
                    project_id=project_id,
                    conversation_id=conversation_id
                )
                repo = DocumentRepository(db_session)
                await repo.create(document_create)
                
                return f"Project summary for {project_key} processed successfully"
                
        except Exception as e:
            logger.error(f"Error processing Jira summary data: {str(e)}")
            raise

class JiraDocumentSource(DocumentSource):
    """Document source for Jira data."""
    
    def __init__(self, data_dir: Optional[str] = None, vector_store_manager=None):
        """Initialize the Jira document source."""
        if data_dir:
            self.data_dir = data_dir
        else:
            # Get the absolute path to the workspace root
            workspace_root = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".."))
            # Construct the path to the data directory
            self.data_dir = os.path.join(workspace_root, "dataset", "4.DataExtraction", "cleaned_data")
            logger.info(f"Jira data directory: {self.data_dir}")
        
        if not vector_store_manager:
            raise ValidationException("Vector store manager is required for Jira document source")
            
        # Initialize the Jira processor with the vector store manager
        self.processor = JiraProcessor(vector_store_manager=vector_store_manager)
        logger.info("JiraProcessor initialized with vector store manager")
    
    async def process_upload(self, file: UploadFile, project_id: Optional[str] = None, conversation_id: Optional[str] = None) -> DocumentData:
        """Process an uploaded Jira JSON file."""
        try:
            # Read file content
            content = await file.read()
            
            # Parse JSON
            jira_data = json.loads(content)
            
            # Process the Jira data using the processor
            summary = await self.processor.process_jira_data(
                data=jira_data,
                file_name=file.filename,
                db_session=self.vector_store.db,
                project_id=project_id,
                conversation_id=conversation_id
            )
            
            # Create a summary document
            return DocumentData(
                title=f"Jira Import Summary - {file.filename}",
                content=summary,
                metadata={
                    'source_type': 'jira',
                    'file_name': file.filename,
                    'document_type': 'summary',
                    'project_id': project_id,
                    'conversation_id': conversation_id
                }
            )
            
        except json.JSONDecodeError:
            raise ValidationException("Invalid JSON file")
        except Exception as e:
            logger.error(f"Error processing Jira file: {str(e)}")
            raise ValidationException(f"Error processing Jira file: {str(e)}")
    
    async def process_document(self, source_id: str) -> DocumentData:
        """Process a Jira document from the source system."""
        try:
            # Parse the source_id to get project and timestamp
            # Format: project_name:timestamp
            parts = source_id.split(":")
            if len(parts) != 2:
                raise ValidationException("Invalid source_id format. Expected 'project_name:timestamp'")
            
            project_name, timestamp = parts
            
            # Find the latest directory if timestamp is 'latest'
            if timestamp == 'latest':
                timestamp = self._get_latest_timestamp()
            
            # Try different file name patterns
            possible_file_names = [
                f"{project_name}.json",
                f"{project_name}_JiraEcosystem.json",
                f"{project_name}_Jira.json"
            ]
            
            file_path = None
            for file_name in possible_file_names:
                temp_path = os.path.join(self.data_dir, timestamp, file_name)
                if os.path.exists(temp_path):
                    file_path = temp_path
                    break
            
            if not file_path:
                # If no exact match, try to find a file that contains the project name
                dir_path = os.path.join(self.data_dir, timestamp)
                if os.path.exists(dir_path):
                    for file_name in os.listdir(dir_path):
                        if file_name.endswith('.json') and project_name in file_name:
                            file_path = os.path.join(dir_path, file_name)
                            break
            
            if not file_path:
                raise ValidationException(f"Jira data file not found for project {project_name} in {timestamp}")
            
            logger.info(f"Processing Jira data file: {file_path}")
            
            # Read and parse the JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                jira_data = json.load(f)
            
            # Process the Jira data using the processor
            summary = await self.processor.process_jira_data(
                data=jira_data,
                file_name=os.path.basename(file_path),
                db_session=self.vector_store.db
            )
            
            # Create a summary document
            return DocumentData(
                title=f"Jira Import Summary - {project_name}",
                content=summary,
                metadata={
                    'source_type': 'jira',
                    'file_name': os.path.basename(file_path),
                    'document_type': 'summary'
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing Jira document: {str(e)}")
            raise ValidationException(f"Error processing Jira document: {str(e)}")
    
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """Validate the source credentials."""
        # For file-based Jira data, we don't need credentials
        return True
    
    def _get_latest_timestamp(self) -> str:
        """Get the latest timestamp directory."""
        try:
            # List all directories in the data directory
            dirs = [d for d in os.listdir(self.data_dir) if os.path.isdir(os.path.join(self.data_dir, d))]
            
            # Sort directories by name (timestamp) in descending order
            dirs.sort(reverse=True)
            
            # Return the latest directory
            if dirs:
                return dirs[0]
            else:
                raise ValidationException("No Jira data directories found")
        except Exception as e:
            logger.error(f"Error getting latest timestamp: {str(e)}")
            raise ValidationException(f"Error getting latest timestamp: {str(e)}") 