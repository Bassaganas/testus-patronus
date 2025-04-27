# dataset/4.DataExtraction/extract_and_clean_jira_data.py
import pymongo
import json
import os
import logging
from pymongo import MongoClient
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
import re
from jira_cleaning_utils import generate_project_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get the absolute path to the dataset directory
DATASET_ROOT = Path(__file__).parent.parent.absolute()

# Configuration
MONGO_DB_NAME = 'JiraRepos'
MONGO_URI = 'mongodb://localhost:27017/'
OUTPUT_DIR = os.path.join(DATASET_ROOT, '4.DataExtraction', 'raw_data')
CLEANED_DIR = os.path.join(DATASET_ROOT, '4.DataExtraction', 'cleaned_data')

# Selected projects based on size and diversity
# These projects have a good balance of issues and represent different domains
PROJECTS_TO_EXTRACT = [
    # Original projects (verified collections)
    #'MongoDB',      # Database (137,000 issues)
    #'Spring',       # Framework (69,000 issues)
    #'JFrog',        # DevOps (16,000 issues)
    'JiraEcosystem', # Atlassian (42,000 issues)
    
    # Additional business-logic focused projects from existing collections
    #'Apache',       # Apache Software Foundation - Various projects
    #'RedHat',       # Enterprise Linux and Open Source
    #'MariaDB',      # Database
    #'IntelDAOS',    # Distributed Asynchronous Object Storage
]

# Optionally specify project keys to extract per collection
PROJECT_KEYS_TO_EXTRACT = {
    # Example:
     'JiraEcosystem': ['REST', 'WEBHOOKS', 'VOTE', 'TOC'],
     'Spring': ['ANDROID', 'DATAJDBC'],
}

def create_output_directories():
    """Create the output directories with timestamp."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_dir = os.path.join(OUTPUT_DIR, timestamp)
    cleaned_dir = os.path.join(CLEANED_DIR, timestamp)
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(cleaned_dir, exist_ok=True)
    return raw_dir, cleaned_dir

def clean_json_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Clean and normalize Jira JSON data.
    
    Args:
        data: List of Jira issue dictionaries
        
    Returns:
        List of cleaned Jira issue dictionaries
    """
    # Check if data is a list
    if not isinstance(data, list):
        logger.warning(f"Expected list but got {type(data)}. Converting to list.")
        data = [data]
    
    cleaned_data = []
    
    for issue in data:
        try:
            # Check if issue is a dictionary
            if not isinstance(issue, dict):
                logger.warning(f"Skipping non-dictionary issue: {type(issue)}")
                continue
                
            # Create a new dict with only the fields we want
            cleaned_issue = {
                "id": issue.get("id"),
                "key": issue.get("key"),
                "fields": {}
            }
            
            # Get the fields dictionary
            fields = issue.get("fields", {})
            
            # Check if fields is a dictionary
            if not isinstance(fields, dict):
                logger.warning(f"Fields is not a dictionary: {type(fields)}")
                fields = {}
            
            # Clean and normalize basic fields
            cleaned_issue["fields"].update({
                "summary": _clean_text(fields.get("summary", "")),
                "description": _clean_text(fields.get("description", "")),
                "status": _clean_status(fields.get("status", {})),
                "priority": _clean_priority(fields.get("priority", {})),
                "issuetype": _clean_issuetype(fields.get("issuetype", {})),
                "created": fields.get("created"),
                "updated": fields.get("updated"),
                "resolutiondate": fields.get("resolutiondate"),
                "labels": fields.get("labels", []),
                "components": _clean_components(fields.get("components", [])),
                "assignee": _clean_user(fields.get("assignee", {})),
                "reporter": _clean_user(fields.get("reporter", {})),
                "issuelinks": _clean_issuelinks(fields.get("issuelinks", [])),
                "customfield_10016": _clean_sprint(fields.get("customfield_10016", {})),
                "customfield_10014": _clean_epic(fields.get("customfield_10014", {})),
                "customfield_10015": _clean_epic_link(fields.get("customfield_10015", {})),
                "customfield_10017": _clean_epic_name(fields.get("customfield_10017", "")),
                "customfield_10018": _clean_epic_status(fields.get("customfield_10018", {})),
                "customfield_10019": _clean_epic_color(fields.get("customfield_10019", {})),
                "customfield_10020": _clean_epic_rank(fields.get("customfield_10020", {})),
                "customfield_10021": _clean_epic_start_date(fields.get("customfield_10021", "")),
                "customfield_10022": _clean_epic_end_date(fields.get("customfield_10022", "")),
                "customfield_10023": _clean_epic_team(fields.get("customfield_10023", {})),
                "customfield_10024": _clean_epic_owner(fields.get("customfield_10024", {})),
                "customfield_10025": _clean_epic_story_points(fields.get("customfield_10025", {})),
                "customfield_10026": _clean_epic_priority(fields.get("customfield_10026", {})),
                "customfield_10027": _clean_epic_risk(fields.get("customfield_10027", {})),
                "customfield_10028": _clean_epic_value(fields.get("customfield_10028", {})),
                "customfield_10029": _clean_epic_dependencies(fields.get("customfield_10029", [])),
                "customfield_10030": _clean_epic_milestones(fields.get("customfield_10030", [])),
                "customfield_10031": _clean_epic_metrics(fields.get("customfield_10031", {})),
                "customfield_10032": _clean_epic_attachments(fields.get("customfield_10032", [])),
                "customfield_10033": _clean_epic_comments(fields.get("customfield_10033", [])),
                "customfield_10034": _clean_epic_watchers(fields.get("customfield_10034", [])),
                "customfield_10035": _clean_epic_voters(fields.get("customfield_10035", [])),
                "customfield_10036": _clean_epic_time_spent(fields.get("customfield_10036", {})),
                "customfield_10037": _clean_epic_time_estimate(fields.get("customfield_10037", {})),
                "customfield_10038": _clean_epic_time_original_estimate(fields.get("customfield_10038", {})),
                "customfield_10039": _clean_epic_time_spent_seconds(fields.get("customfield_10039", 0)),
                "customfield_10040": _clean_epic_time_estimate_seconds(fields.get("customfield_10040", 0)),
                "customfield_10041": _clean_epic_time_original_estimate_seconds(fields.get("customfield_10041", 0)),
                "customfield_10042": _clean_epic_time_spent_formatted(fields.get("customfield_10042", "")),
                "customfield_10043": _clean_epic_time_estimate_formatted(fields.get("customfield_10043", "")),
                "customfield_10044": _clean_epic_time_original_estimate_formatted(fields.get("customfield_10044", "")),
                "customfield_10045": _clean_epic_time_spent_seconds_formatted(fields.get("customfield_10045", "")),
                "customfield_10046": _clean_epic_time_estimate_seconds_formatted(fields.get("customfield_10046", "")),
                "customfield_10047": _clean_epic_time_original_estimate_seconds_formatted(fields.get("customfield_10047", "")),
                "customfield_10048": _clean_epic_time_spent_seconds_formatted(fields.get("customfield_10048", "")),
                "customfield_10049": _clean_epic_time_estimate_seconds_formatted(fields.get("customfield_10049", "")),
                "customfield_10050": _clean_epic_time_original_estimate_seconds_formatted(fields.get("customfield_10050", ""))
            })
            
            # Remove None values and empty strings
            cleaned_issue["fields"] = {k: v for k, v in cleaned_issue["fields"].items() if v is not None and v != ""}
            
            # Add the cleaned issue to the list
            cleaned_data.append(cleaned_issue)
            
        except Exception as e:
            logger.error(f"Error cleaning issue {issue.get('key', 'unknown')}: {str(e)}")
            continue
    
    return cleaned_data

def _clean_text(text: str) -> str:
    """Clean and normalize text fields."""
    if not text:
        return ""
    
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters
    text = re.sub(r'[^\w\s.,;:!?()-]', '', text)
    
    return text.strip()

def _clean_status(status: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize status field."""
    if not status:
        return {}
    
    return {
        "id": status.get("id"),
        "name": status.get("name", "").strip(),
        "statusCategory": {
            "id": status.get("statusCategory", {}).get("id"),
            "name": status.get("statusCategory", {}).get("name", "").strip()
        }
    }

def _clean_priority(priority: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize priority field."""
    if not priority:
        return {}
    
    return {
        "id": priority.get("id"),
        "name": priority.get("name", "").strip(),
        "iconUrl": priority.get("iconUrl")
    }

def _clean_issuetype(issuetype: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize issue type field."""
    if not issuetype:
        return {}
    
    return {
        "id": issuetype.get("id"),
        "name": issuetype.get("name", "").strip(),
        "description": _clean_text(issuetype.get("description", "")),
        "iconUrl": issuetype.get("iconUrl")
    }

def _clean_components(components: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize components field."""
    if not components:
        return []
    
    cleaned_components = []
    for component in components:
        if component:
            cleaned_components.append({
                "id": component.get("id"),
                "name": component.get("name", "").strip(),
                "description": _clean_text(component.get("description", ""))
            })
    
    return cleaned_components

def _clean_user(user: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize user fields."""
    if not user:
        return {}
    
    return {
        "accountId": user.get("accountId"),
        "displayName": user.get("displayName", "").strip(),
        "emailAddress": user.get("emailAddress"),
        "active": user.get("active", False)
    }

def _clean_issuelinks(issuelinks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize issue links field."""
    if not issuelinks:
        return []
    
    cleaned_links = []
    for link in issuelinks:
        if link:
            cleaned_link = {
                "id": link.get("id"),
                "type": {
                    "id": link.get("type", {}).get("id"),
                    "name": link.get("type", {}).get("name", "").strip()
                }
            }
            
            # Clean inward issue
            if "inwardIssue" in link:
                cleaned_link["inwardIssue"] = {
                    "id": link["inwardIssue"].get("id"),
                    "key": link["inwardIssue"].get("key"),
                    "fields": {
                        "summary": _clean_text(link["inwardIssue"].get("fields", {}).get("summary", "")),
                        "status": _clean_status(link["inwardIssue"].get("fields", {}).get("status", {}))
                    }
                }
            
            # Clean outward issue
            if "outwardIssue" in link:
                cleaned_link["outwardIssue"] = {
                    "id": link["outwardIssue"].get("id"),
                    "key": link["outwardIssue"].get("key"),
                    "fields": {
                        "summary": _clean_text(link["outwardIssue"].get("fields", {}).get("summary", "")),
                        "status": _clean_status(link["outwardIssue"].get("fields", {}).get("status", {}))
                    }
                }
            
            cleaned_links.append(cleaned_link)
    
    return cleaned_links

def _clean_sprint(sprint: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize sprint field."""
    if not sprint:
        return {}
    
    return {
        "id": sprint.get("id"),
        "name": sprint.get("name", "").strip(),
        "state": sprint.get("state", "").strip(),
        "startDate": sprint.get("startDate"),
        "endDate": sprint.get("endDate"),
        "completeDate": sprint.get("completeDate"),
        "goal": _clean_text(sprint.get("goal", ""))
    }

def _clean_epic(epic: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic field."""
    if not epic:
        return {}
    
    return {
        "id": epic.get("id"),
        "key": epic.get("key"),
        "name": epic.get("name", "").strip(),
        "summary": _clean_text(epic.get("summary", "")),
        "description": _clean_text(epic.get("description", "")),
        "status": _clean_status(epic.get("status", {})),
        "priority": _clean_priority(epic.get("priority", {})),
        "assignee": _clean_user(epic.get("assignee", {})),
        "reporter": _clean_user(epic.get("reporter", {})),
        "created": epic.get("created"),
        "updated": epic.get("updated"),
        "resolutiondate": epic.get("resolutiondate")
    }

def _clean_epic_link(epic_link: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic link field."""
    if not epic_link:
        return {}
    
    return {
        "id": epic_link.get("id"),
        "key": epic_link.get("key"),
        "name": epic_link.get("name", "").strip(),
        "summary": _clean_text(epic_link.get("summary", "")),
        "status": _clean_status(epic_link.get("status", {}))
    }

def _clean_epic_name(epic_name: str) -> str:
    """Clean and normalize epic name field."""
    return _clean_text(epic_name)

def _clean_epic_status(epic_status: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic status field."""
    if not epic_status:
        return {}
    
    return {
        "id": epic_status.get("id"),
        "name": epic_status.get("name", "").strip(),
        "statusCategory": {
            "id": epic_status.get("statusCategory", {}).get("id"),
            "name": epic_status.get("statusCategory", {}).get("name", "").strip()
        }
    }

def _clean_epic_color(epic_color: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic color field."""
    if not epic_color:
        return {}
    
    return {
        "key": epic_color.get("key"),
        "value": epic_color.get("value")
    }

def _clean_epic_rank(epic_rank: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic rank field."""
    if not epic_rank:
        return {}
    
    return {
        "rank": epic_rank.get("rank"),
        "oldRank": epic_rank.get("oldRank")
    }

def _clean_epic_start_date(date: str) -> str:
    """Clean and normalize epic start date field."""
    if not date:
        return ""
    
    try:
        # Parse and format the date
        parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        return parsed_date.strftime("%Y-%m-%d")
    except:
        return ""

def _clean_epic_end_date(date: str) -> str:
    """Clean and normalize epic end date field."""
    if not date:
        return ""
    
    try:
        # Parse and format the date
        parsed_date = datetime.fromisoformat(date.replace('Z', '+00:00'))
        return parsed_date.strftime("%Y-%m-%d")
    except:
        return ""

def _clean_epic_team(team: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic team field."""
    if not team:
        return {}
    
    return {
        "id": team.get("id"),
        "name": team.get("name", "").strip(),
        "type": team.get("type", "").strip()
    }

def _clean_epic_owner(owner: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic owner field."""
    return _clean_user(owner)

def _clean_epic_story_points(points: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic story points field."""
    if not points:
        return {}
    
    return {
        "value": points.get("value"),
        "oldValue": points.get("oldValue")
    }

def _clean_epic_priority(priority: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic priority field."""
    return _clean_priority(priority)

def _clean_epic_risk(risk: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic risk field."""
    if not risk:
        return {}
    
    return {
        "id": risk.get("id"),
        "value": risk.get("value", "").strip()
    }

def _clean_epic_value(value: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic value field."""
    if not value:
        return {}
    
    return {
        "id": value.get("id"),
        "value": value.get("value", "").strip()
    }

def _clean_epic_dependencies(dependencies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize epic dependencies field."""
    if not dependencies:
        return []
    
    cleaned_dependencies = []
    for dep in dependencies:
        if dep:
            cleaned_dependencies.append({
                "id": dep.get("id"),
                "key": dep.get("key"),
                "name": dep.get("name", "").strip(),
                "type": dep.get("type", "").strip()
            })
    
    return cleaned_dependencies

def _clean_epic_milestones(milestones: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize epic milestones field."""
    if not milestones:
        return []
    
    cleaned_milestones = []
    for milestone in milestones:
        if milestone:
            cleaned_milestones.append({
                "id": milestone.get("id"),
                "name": milestone.get("name", "").strip(),
                "startDate": _clean_epic_start_date(milestone.get("startDate", "")),
                "endDate": _clean_epic_end_date(milestone.get("endDate", "")),
                "status": milestone.get("status", "").strip()
            })
    
    return cleaned_milestones

def _clean_epic_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic metrics field."""
    if not metrics:
        return {}
    
    return {
        "progress": metrics.get("progress", 0),
        "total": metrics.get("total", 0),
        "completed": metrics.get("completed", 0),
        "remaining": metrics.get("remaining", 0)
    }

def _clean_epic_attachments(attachments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize epic attachments field."""
    if not attachments:
        return []
    
    cleaned_attachments = []
    for attachment in attachments:
        if attachment:
            cleaned_attachments.append({
                "id": attachment.get("id"),
                "filename": attachment.get("filename", "").strip(),
                "size": attachment.get("size", 0),
                "mimeType": attachment.get("mimeType", "").strip(),
                "content": attachment.get("content", "").strip(),
                "created": attachment.get("created")
            })
    
    return cleaned_attachments

def _clean_epic_comments(comments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize epic comments field."""
    if not comments:
        return []
    
    cleaned_comments = []
    for comment in comments:
        if comment:
            cleaned_comments.append({
                "id": comment.get("id"),
                "body": _clean_text(comment.get("body", "")),
                "author": _clean_user(comment.get("author", {})),
                "created": comment.get("created"),
                "updated": comment.get("updated")
            })
    
    return cleaned_comments

def _clean_epic_watchers(watchers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize epic watchers field."""
    if not watchers:
        return []
    
    cleaned_watchers = []
    for watcher in watchers:
        if watcher:
            cleaned_watchers.append(_clean_user(watcher))
    
    return cleaned_watchers

def _clean_epic_voters(voters: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and normalize epic voters field."""
    if not voters:
        return []
    
    cleaned_voters = []
    for voter in voters:
        if voter:
            cleaned_voters.append(_clean_user(voter))
    
    return cleaned_voters

def _clean_epic_time_spent(time_spent: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic time spent field."""
    if not time_spent:
        return {}
    
    return {
        "seconds": time_spent.get("seconds", 0),
        "formatted": time_spent.get("formatted", "").strip()
    }

def _clean_epic_time_estimate(time_estimate: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic time estimate field."""
    if not time_estimate:
        return {}
    
    return {
        "seconds": time_estimate.get("seconds", 0),
        "formatted": time_estimate.get("formatted", "").strip()
    }

def _clean_epic_time_original_estimate(time_original_estimate: Dict[str, Any]) -> Dict[str, Any]:
    """Clean and normalize epic time original estimate field."""
    if not time_original_estimate:
        return {}
    
    return {
        "seconds": time_original_estimate.get("seconds", 0),
        "formatted": time_original_estimate.get("formatted", "").strip()
    }

def _clean_epic_time_spent_seconds(seconds: int) -> int:
    """Clean and normalize epic time spent seconds field."""
    return seconds if seconds else 0

def _clean_epic_time_estimate_seconds(seconds: int) -> int:
    """Clean and normalize epic time estimate seconds field."""
    return seconds if seconds else 0

def _clean_epic_time_original_estimate_seconds(seconds: int) -> int:
    """Clean and normalize epic time original estimate seconds field."""
    return seconds if seconds else 0

def _clean_epic_time_spent_formatted(formatted: str) -> str:
    """Clean and normalize epic time spent formatted field."""
    return formatted.strip() if formatted else ""

def _clean_epic_time_estimate_formatted(formatted: str) -> str:
    """Clean and normalize epic time estimate formatted field."""
    return formatted.strip() if formatted else ""

def _clean_epic_time_original_estimate_formatted(formatted: str) -> str:
    """Clean and normalize epic time original estimate formatted field."""
    return formatted.strip() if formatted else ""

def _clean_epic_time_spent_seconds_formatted(formatted: str) -> str:
    """Clean and normalize epic time spent seconds formatted field."""
    return formatted.strip() if formatted else ""

def _clean_epic_time_estimate_seconds_formatted(formatted: str) -> str:
    """Clean and normalize epic time estimate seconds formatted field."""
    return formatted.strip() if formatted else ""

def _clean_epic_time_original_estimate_seconds_formatted(formatted: str) -> str:
    """Clean and normalize epic time original estimate seconds formatted field."""
    return formatted.strip() if formatted else ""

def extract_and_clean_project_data(collection, raw_dir, cleaned_dir, target_project=None, allowed_project_keys=None, generate_summary=False):
    """
    Extract data from a project collection, save raw data, and clean it.
    Optionally filter to only allowed_project_keys.
    
    Args:
        collection: MongoDB collection
        raw_dir: Directory to save raw data
        cleaned_dir: Directory to save cleaned data
        target_project: Optional project key to filter issues
        allowed_project_keys: Optional list of project keys to filter issues
        
    Returns:
        dict: Statistics about the extraction and cleaning process
    """
    project_name = collection.name
    print(f"\nProcessing project: {project_name}")
    
    # Get total count for progress tracking
    total_docs = collection.count_documents({})
    print(f"Total documents to process: {total_docs}")
    
    # Extract and clean documents in batches to manage memory
    batch_size = 1000
    raw_documents = []
    cleaned_documents = []
    
    for i in range(0, total_docs, batch_size):
        batch = list(collection.find(
            {},
            {'_id': 0},  # Exclude MongoDB's _id field
            skip=i,
            limit=batch_size
        ))
        raw_documents.extend(batch)
        
        # Clean each document individually
        for doc in batch:
            try:
                # clean_json_data already returns a list, so we just extend with it directly
                cleaned_documents.extend(clean_json_data(doc))
            except Exception as e:
                logger.error(f"Error cleaning document: {str(e)}")
                continue
                
        print(f"Processed {min(i + batch_size, total_docs)}/{total_docs} documents")
    
    # Group documents by project key
    projects = {}
    for doc in cleaned_documents:
        # Extract project key from issue key (e.g., "PROJ-123" -> "PROJ")
        issue_key = doc.get('key', '')
        if issue_key:
            project_key = issue_key.split('-')[0]
        else:
            # Fallback to project field
            project = doc.get('fields', {}).get('project', {})
            project_key = project.get('key', 'UNKNOWN')
        if allowed_project_keys and project_key not in allowed_project_keys:
            continue
        if project_key not in projects:
            projects[project_key] = []
        projects[project_key].append(doc)
    
    # If target project is specified, filter to just that project
    if target_project:
        if target_project not in projects:
            print(f"Warning: Project {target_project} not found in the data")
            return {
                'raw_count': len(raw_documents),
                'cleaned_count': 0,
                'raw_size_mb': 0,
                'cleaned_size_mb': 0,
                'reduction_percent': 0,
                'projects': {}
            }
        projects = {target_project: projects[target_project]}
    
    # Save raw data
    raw_file = os.path.join(raw_dir, f'{project_name}.json')
    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(raw_documents, f, ensure_ascii=False, indent=2)
    
    # Save cleaned data for each project
    project_stats = {}
    for project_key, project_docs in projects.items():
        # Save per-issue cleaned docs with collection name included
        cleaned_file = os.path.join(cleaned_dir, f'{project_key}_{project_name}_issues.json')
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            json.dump(project_docs, f, ensure_ascii=False, indent=2)
        print(f"Saved per-issue file: {cleaned_file}")
        
        # Generate and save project summary doc (LLM-based or fallback)
        if generate_summary:
            summary_doc = generate_project_summary(project_key, project_docs, use_llm=True)  # or use_llm=False for fallback
            summary_file = os.path.join(cleaned_dir, f'{project_key}_{project_name}_SUMMARY.json')
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump([summary_doc], f, ensure_ascii=False, indent=2)
            print(f"Saved summary file: {summary_file}")
        
        # Calculate size for this project
        cleaned_size = os.path.getsize(cleaned_file) / (1024 * 1024)  # MB
        
        # Store stats for this project
        project_stats[project_key] = {
            'document_count': len(project_docs),
            'size_mb': cleaned_size
        }
        
        print(f"Saved {len(project_docs)} documents for project {project_key} in {project_name} ({cleaned_size:.2f}MB)")
    
    # Calculate overall stats
    raw_size = os.path.getsize(raw_file) / (1024 * 1024)  # MB
    total_cleaned_size = sum(stats['size_mb'] for stats in project_stats.values())
    reduction = ((raw_size - total_cleaned_size) / raw_size) * 100 if raw_size > 0 else 0
    
    print(f"Raw data saved: {raw_size:.2f}MB")
    print(f"Total cleaned data saved: {total_cleaned_size:.2f}MB")
    print(f"Size reduction: {reduction:.2f}%")
    
    return {
        'raw_count': len(raw_documents),
        'cleaned_count': len(cleaned_documents),
        'raw_size_mb': raw_size,
        'cleaned_size_mb': total_cleaned_size,
        'reduction_percent': reduction,
        'projects': project_stats
    }

def main():
    # Create output directories with timestamp
    raw_dir, cleaned_dir = create_output_directories()
    print(f"Created output directories:")
    print(f"Raw data: {raw_dir}")
    print(f"Cleaned data: {cleaned_dir}")
    
    # Connect to MongoDB
    print(f"\nConnecting to MongoDB at {MONGO_URI}...")
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]
    
    # Get available collections
    available_collections = db.list_collection_names()
    print("\nAvailable collections in database:")
    for collection in available_collections:
        print(f"- {collection}")
    
    # Process each project
    results = {}
    for project_name in PROJECTS_TO_EXTRACT:
        try:
            if project_name not in available_collections:
                print(f"\nWarning: Collection '{project_name}' not found in database. Skipping...")
                results[project_name] = "Collection not found"
                continue
                
            collection = db[project_name]
            allowed_keys = PROJECT_KEYS_TO_EXTRACT.get(project_name)
            stats = extract_and_clean_project_data(collection, raw_dir, cleaned_dir, allowed_project_keys=allowed_keys)
            results[project_name] = stats
        except Exception as e:
            print(f"Error processing {project_name}: {str(e)}")
            results[project_name] = f"Error: {str(e)}"
    
    # Save summary
    summary = {
        'timestamp': datetime.now().isoformat(),
        'projects_processed': results,
        'available_collections': available_collections,
        'project_categories': {
            'databases': ['MongoDB', 'MariaDB'],
            'frameworks': ['Spring', 'Qt'],
            'devops': ['JFrog', 'RedHat'],
            'security': ['Sonatype'],
            'blockchain': ['Hyperledger'],
            'storage': ['IntelDAOS'],
            'ecosystem': ['JiraEcosystem', 'Apache'],
            'virtual_worlds': ['SecondLife']
        }
    }
    
    # Save summary to both directories
    for directory in [raw_dir, cleaned_dir]:
        summary_file = os.path.join(directory, 'extraction_summary.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
    
    print("\nExtraction and Cleaning Summary:")
    for project, stats in results.items():
        if isinstance(stats, dict):
            print(f"\n{project}:")
            print(f"  Raw documents: {stats['raw_count']}")
            print(f"  Cleaned documents: {stats['cleaned_count']}")
            print(f"  Raw size: {stats['raw_size_mb']:.2f}MB")
            print(f"  Cleaned size: {stats['cleaned_size_mb']:.2f}MB")
            print(f"  Size reduction: {stats['reduction_percent']:.2f}%")
            print("\n  Projects:")
            for proj_key, proj_stats in stats.get('projects', {}).items():
                print(f"    {proj_key}:")
                print(f"      Documents: {proj_stats['document_count']}")
                print(f"      Size: {proj_stats['size_mb']:.2f}MB")
        else:
            print(f"{project}: {stats}")
            
if __name__ == '__main__':
    main() 