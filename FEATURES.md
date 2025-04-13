# Testus Patronus - New Features Guide

This guide will walk you through the enhanced user interface and features now available in Testus Patronus.

## Interface Overview

The application now has a two-panel layout:

1. **Sidebar** (left panel) - Contains your projects and conversations
2. **Main Content Area** (right panel) - Contains the chat interface and document view

## Projects and Conversations Management

### Creating Projects and Conversations

- **Create a Project**: Click the "+ Project" button at the top of the sidebar
- **Create a Conversation**: 
  - Click the "+ Conversation" button at the top of the sidebar (for standalone conversations)
  - Click the "+" icon next to any project to create a conversation within that project

### Managing Projects

Projects are containers that can hold multiple conversations. They help you organize related conversations.

- **Select a Project**: Click on any project in the sidebar to view its details and documents
- **Delete a Project**: Click the trash icon next to a project name (this will delete all conversations within the project)

### Managing Conversations

Conversations are individual chat sessions where you can ask questions about documents.

- **Select a Conversation**: Click on any conversation in the sidebar to view its messages and documents
- **Delete a Conversation**: Click the trash icon next to a conversation name

## Drag and Drop Organization

You can easily reorganize your conversations:

1. **Move a Conversation to a Project**: 
   - Click and drag any standalone conversation
   - Drop it onto a project to add it to that project

2. **Move a Conversation out of a Project**:
   - Click and drag a conversation from within a project
   - Drop it in the "Conversations" section to make it standalone

## Document Management

Documents can be associated with projects or conversations. The system will use the appropriate context when answering your questions.

### Viewing Documents

1. Click "Show Documents" at the top of the main panel to see documents associated with the current project or conversation

### Uploading Documents

1. In the chat interface, click the "Upload Document" button
2. Select a document to upload (PDF, TXT, MD, or HTML)
3. The document will be processed and associated with the current conversation or project

### Document List Features

The document list shows:
- Document name
- Document type (PDF, TXT, etc.)
- File size
- Delete button for removing documents

## Asking Questions

1. Select a conversation or project
2. Type your question in the input field at the bottom of the chat
3. The system will use the documents in the current context to generate answers

## Tips for Best Results

1. **Organize by Topic**: Create projects for specific topics or domains
2. **Relevant Documents**: Upload documents that are relevant to the questions you plan to ask
3. **Be Specific**: Ask clear, specific questions for better results
4. **Review Documents**: Check which documents are in context before asking questions

## Troubleshooting

If you encounter issues:

1. Make sure the backend server is running (`uvicorn app.main:app --reload`)
2. Make sure the frontend is running (`npm start`)
3. Check browser console for errors (F12 → Console tab)
4. Try refreshing the page after creating new projects or conversations 