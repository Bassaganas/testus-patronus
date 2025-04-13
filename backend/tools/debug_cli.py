#!/usr/bin/env python
"""
Debug CLI Tool for Testus Patronus
This tool provides debugging and database inspection capabilities.
"""

import os
import sys
import json
import logging
import click
from tabulate import tabulate
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import app modules
from app.config import settings
from app.db.session import engine
from app.models import Project, Conversation, Document
from app.db.models import Project as DBProject, Conversation as DBConversation
from app.vector_store import VectorStoreManager
from app.rag_chain import RAGChain

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("testus-patronus-debug")

def format_timestamp(value):
    """Format timestamp values"""
    try:
        return datetime.fromisoformat(value).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return value

def execute_query(query: str, params: dict = None):
    """Execute a query and print results in a table format"""
    with engine.connect() as connection:
        result = connection.execute(text(query), params if params else {})
        rows = result.fetchall()
        if rows:
            columns = result.keys()
            # Format timestamps in the results
            formatted_rows = []
            for row in rows:
                formatted_row = [format_timestamp(value) if isinstance(value, str) and 'time' in col.lower() 
                               else value for col, value in zip(columns, row)]
                formatted_rows.append(formatted_row)
            
            print("\n" + tabulate(formatted_rows, headers=columns, tablefmt="grid"))
            print(f"\nTotal rows: {len(rows)}")
        else:
            print("\nNo results found.")

@click.group()
def cli():
    """Debug CLI tool for Testus Patronus"""
    pass

@cli.command()
def tables():
    """List all tables in the database"""
    query = """
    SELECT name as table_name 
    FROM sqlite_master 
    WHERE type='table' 
    ORDER BY name;
    """
    print("\nAvailable tables:")
    execute_query(query)

@cli.command()
@click.argument('table_name')
def schema(table_name):
    """Show schema for a specific table"""
    query = f"""
    SELECT sql 
    FROM sqlite_master 
    WHERE type='table' AND name='{table_name}';
    """
    execute_query(query)

@cli.command()
def activity():
    """Show recent activity across all tables"""
    query = """
    SELECT 
        'Project' as type,
        title as name,
        created_at
    FROM projects 
    WHERE created_at > datetime('now', '-1 day')
    UNION ALL
    SELECT 
        'Conversation' as type,
        title as name,
        created_at
    FROM conversations 
    WHERE created_at > datetime('now', '-1 day')
    UNION ALL
    SELECT 
        'Document' as type,
        title as name,
        created_at
    FROM documents 
    WHERE created_at > datetime('now', '-1 day')
    ORDER BY created_at DESC;
    """
    execute_query(query)

@cli.command()
def projects():
    """Show projects summary with conversation and document counts"""
    query = """
    SELECT 
        p.title as project_title,
        p.description,
        COUNT(DISTINCT c.id) as conversation_count,
        COUNT(DISTINCT d.id) as document_count,
        p.created_at
    FROM projects p
    LEFT JOIN conversations c ON c.project_id = p.id
    LEFT JOIN documents d ON d.project_id = p.id
    GROUP BY p.id
    ORDER BY p.created_at DESC;
    """
    execute_query(query)

@cli.command()
def test_rag():
    """Test RAG chain functionality"""
    vector_store = VectorStoreManager()
    rag_chain = RAGChain(vector_store)
    
    query = "What is the capital of France?"
    print(f"\nTesting RAG chain with query: {query}")
    
    response = rag_chain.get_response(query)
    print(f"\nResponse: {response}")

@cli.command()
@click.argument('query')
def custom(query):
    """Execute a custom SQL query"""
    execute_query(query)

if __name__ == "__main__":
    cli() 