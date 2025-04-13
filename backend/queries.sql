-- List all tables
SELECT name as table_name 
FROM sqlite_master 
WHERE type='table' 
ORDER BY name;

-- Show projects with stats
SELECT 
    p.title as project_title,
    p.description,
    COUNT(DISTINCT c.id) as conversation_count,
    COUNT(DISTINCT d.id) as document_count,
    datetime(p.created_at) as created_at
FROM projects p
LEFT JOIN conversations c ON c.project_id = p.id
LEFT JOIN documents d ON d.project_id = p.id
GROUP BY p.id
ORDER BY p.created_at DESC;

-- Show conversations with messages
SELECT 
    c.title as conversation_title,
    p.title as project_title,
    json_array_length(c.messages) as message_count,
    datetime(c.created_at) as created_at
FROM conversations c
JOIN projects p ON c.project_id = p.id
ORDER BY c.created_at DESC;

-- Show recent activity
SELECT 
    'Project' as type,
    title as name,
    datetime(created_at) as created_at
FROM projects 
WHERE created_at > datetime('now', '-1 day')
UNION ALL
SELECT 
    'Conversation' as type,
    title as name,
    datetime(created_at) as created_at
FROM conversations 
WHERE created_at > datetime('now', '-1 day')
UNION ALL
SELECT 
    'Document' as type,
    title as name,
    datetime(created_at) as created_at
FROM documents 
WHERE created_at > datetime('now', '-1 day')
ORDER BY created_at DESC;

-- Show documents by project
SELECT 
    d.title as document_title,
    d.file_name,
    d.file_type,
    d.file_size,
    p.title as project_title,
    c.title as conversation_title,
    datetime(d.created_at) as created_at
FROM documents d
LEFT JOIN projects p ON d.project_id = p.id
LEFT JOIN conversations c ON d.conversation_id = c.id
ORDER BY d.created_at DESC;

-- Show project details
SELECT 
    p.title as project_title,
    p.description,
    datetime(p.created_at) as created_at,
    datetime(p.updated_at) as updated_at,
    GROUP_CONCAT(DISTINCT c.title) as conversations,
    GROUP_CONCAT(DISTINCT d.title) as documents
FROM projects p
LEFT JOIN conversations c ON c.project_id = p.id
LEFT JOIN documents d ON d.project_id = p.id
GROUP BY p.id
ORDER BY p.created_at DESC; 