import re
import openai
import json
from pathlib import Path
from collections import defaultdict
import logging
import os
from dotenv import load_dotenv
import random
import asyncio

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def load_and_group_issues_by_project(input_files):
    """
    Given a list of JSON file paths, load all issues and group them by project key.
    Returns: dict of {project_key: [issues]}
    """
    all_project_docs = []
    for input_file in input_files:
        with open(input_file, "r", encoding="utf-8") as f:
            try:
                docs = json.load(f)
                if isinstance(docs, dict):
                    docs = [docs]
                all_project_docs.extend(docs)
            except Exception as e:
                print(f"Error reading {input_file}: {e}")
    projects = defaultdict(list)
    for doc in all_project_docs:
        key = doc.get("key", "")
        project_key = key.split("-")[0] if "-" in key else "UNKNOWN"
        projects[project_key].append(doc)
    return projects

def sample_issues(project_docs, sample_size=300):
    """Randomly sample a subset of issues for summarization, ensuring description is not empty and at least 50 characters."""
    filtered_docs = [
        issue for issue in project_docs
        if len((issue.get("fields", {}).get("description", "") or "")) >= 50
    ]
    if len(filtered_docs) > sample_size:
        return random.sample(filtered_docs, sample_size)
    return filtered_docs

def batch_summarize_issues(project_key, project_docs, batch_size=100, max_desc_len=400, max_summary_len=500):
    """Synchronous version of batch summarization, including both summaries and descriptions."""
    batch_summaries = []
    for i in range(0, len(project_docs), batch_size):
        batch = project_docs[i:i+batch_size]
        all_summaries = [
            (issue.get("fields", {}).get("summary", "") or "")[:max_summary_len]
            for issue in batch if issue.get("fields", {}).get("summary", "")
        ]
        all_descriptions = [
            (issue.get("fields", {}).get("description", "") or "")[:max_desc_len]
            for issue in batch if issue.get("fields", {}).get("description", "")
        ]
        batch_summary = call_llm_for_summary(project_key, all_summaries, all_descriptions)
        batch_summaries.append(batch_summary)
    return batch_summaries

def generate_project_summary(project_key, project_docs, use_llm=True):
    all_summaries = []
    all_descriptions = []
    assignees = set()
    reporters = set()
    components = set()
    issues = sample_issues(project_docs=project_docs)
    for issue in issues:
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        description = fields.get("description", "")
        all_summaries.append(summary)
        all_descriptions.append(description)
        assignee = fields.get("assignee", {}).get("displayName")
        reporter = fields.get("reporter", {}).get("displayName")
        if assignee:
            assignees.add(assignee)
        if reporter:
            reporters.add(reporter)
        for comp in fields.get("components", []):
            name = comp.get("name")
            if name:
                components.add(name)
    if use_llm:
        logger.info("Calling llm in batches")
        batch_summaries = batch_summarize_issues(project_key, issues, batch_size=50, max_desc_len=400, max_summary_len=200)
        # Now summarize the batch summaries
        logger.info("Calling final summary {batch_summaries}")
        final_summary = call_llm_for_project_summary(project_key, batch_summaries)
        summary_text = final_summary
    else:
        summary_text = (
            f"Project {project_key} contains {len(project_docs)} issues. "
            f"Summaries: {'; '.join(all_summaries[:5])}...\n"
            f"Descriptions: {'; '.join(all_descriptions[:5])}..."
        )
    summary_doc = {
        "id": f"{project_key}_SUMMARY",
        "key": f"{project_key}-SUMMARY",
        "fields": {
            "summary": summary_text,
            "contributors": sorted(assignees | reporters),
            "assignees": sorted(assignees),
            "reporters": sorted(reporters),
            "components": sorted(components),
            "issue_count": len(project_docs),
            "type": "project_summary"
        }
    }
    return summary_doc

def call_llm_for_summary(project_key, all_summaries, all_descriptions):
    prompt = (
        f"Summarize the following Jira issues for project {project_key}.\n"
        f"Issue descriptions:\n{'; '.join(all_descriptions)}"
    )
    # Check if Azure OpenAI API key is available
    api_key = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
    api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_CHAT_API_VERSION")
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    model_name = "gpt-35-turbo-16k"  # Or whatever model family your deployment uses

    if not api_key or not api_base or not api_version or not deployment_name:
        logger.warning("Azure OpenAI environment variables not set. Using fallback summary.")
        return (
            f"Project {project_key} contains {len(all_summaries)} issues. "
            f"Summaries: {'; '.join(all_summaries[:5])}...\n"
            f"Descriptions: {'; '.join(all_descriptions[:5])}..."
        )

    openai.api_type = "azure"
    openai.api_base = api_base
    openai.api_version = api_version
    openai.api_key = api_key

    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes software projects and products. Be specific, detailed, and concrete and give an overview of the project features from the issues descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return (
            f"Project {project_key} contains {len(all_summaries)} issues. "
            f"Summaries: {'; '.join(all_summaries[:5])}...\n"
            f"Descriptions: {'; '.join(all_descriptions[:5])}..."
        )

def call_llm_for_project_summary(project_key, batch_summaries):
    prompt = (
        f"Given the following summaries of batches of issues from the Jira project {project_key}, "
        "write a high-level, holistic summary of the project. "
        "Focus on the main goals, features, challenges, and overall status of the project, "
        "rather than listing individual issues. Be concise, insightful, and avoid repeating details."
        f"\n\nBatch Summaries:\n{'; '.join(batch_summaries)}"
    )
    # Check if Azure OpenAI API key is available
    api_key = os.getenv("AZURE_OPENAI_CHAT_API_KEY")
    api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_version = os.getenv("AZURE_OPENAI_CHAT_API_VERSION")
    deployment_name = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME")
    model_name = "gpt-35-turbo-16k"  # Or whatever model family your deployment uses

    if not api_key or not api_base or not api_version or not deployment_name:
        logger.warning("Azure OpenAI environment variables not set. Using fallback summary.")
        return (
            f"Project {project_key} contains {len(batch_summaries)} issues. "
            f"Summaries: {'; '.join(batch_summaries[:5])}..."
        )

    openai.api_type = "azure"
    openai.api_base = api_base
    openai.api_version = api_version
    openai.api_key = api_key

    try:
        response = openai.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes software projects and products. Be specific, detailed, and concrete and give an overview of the project features from the issues descriptions."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        return (
            f"Project {project_key} contains {len(batch_summaries)} issues. "
            f"Summaries: {'; '.join(batch_summaries[:5])}..."
        )