import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';

interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
}

const Chat: React.FC = () => {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!input.trim()) return;

        const userMessage: Message = {
            role: 'user',
            content: input,
            timestamp: new Date()
        };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsLoading(true);

        // Create the request payload exactly as the backend's ChatRequest model expects it
        const requestData = {
            query: input.trim()
        };

        try {
            const apiUrl = `${process.env.REACT_APP_API_URL}/api/v1/query`;
            console.log('API URL:', apiUrl);
            console.log('Request payload:', JSON.stringify(requestData, null, 2));
            console.log('Request headers:', {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            });

            // First, try to upload a test document if none exists
            try {
                const testDoc = new File(
                    ['This is a test document to initialize the system.'],
                    'test.txt',
                    { type: 'text/plain' }
                );
                const formData = new FormData();
                formData.append('file', testDoc);
                console.log('Uploading test document...');
                await axios.post(`${process.env.REACT_APP_API_URL}/api/v1/upload`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });
                console.log('Test document uploaded successfully');
            } catch (uploadError) {
                console.log('Test document might already exist:', uploadError);
            }

            // Now send the query
            console.log('Sending query to backend...');
            const response = await axios({
                method: 'POST',
                url: apiUrl,
                data: requestData,
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            });

            console.log('Response:', response.data);
            const botMessage: Message = {
                role: 'assistant',
                content: response.data.response,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error: any) {
            console.error('Full error object:', error);
            console.error('Error details:', {
                message: error.message,
                response: error.response?.data,
                status: error.response?.status,
                headers: error.response?.headers,
                sentData: JSON.stringify(requestData, null, 2)
            });

            if (error.response?.data?.detail) {
                console.error('FastAPI Validation Error:', JSON.stringify(error.response.data.detail, null, 2));
            }

            const errorMessage: Message = {
                role: 'assistant',
                content: `Error: ${error.response?.data?.detail?.[0]?.msg || error.message || 'Unknown error occurred'}`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Check file size (10MB limit)
        const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB in bytes
        if (file.size > MAX_FILE_SIZE) {
            const errorMessage: Message = {
                role: 'assistant',
                content: `Error: File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds maximum limit of 10MB`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        setIsLoading(true);

        try {
            console.log('Uploading file to:', `${process.env.REACT_APP_API_URL}/api/v1/upload`);
            const response = await axios.post(
                `${process.env.REACT_APP_API_URL}/api/v1/upload`,
                formData,
                {
                    headers: {
                        'Content-Type': 'multipart/form-data',
                    },
                    timeout: 30000, // 30 second timeout
                    maxContentLength: MAX_FILE_SIZE,
                    maxBodyLength: MAX_FILE_SIZE
                }
            );

            console.log('Upload response:', response.data);
            const successMessage: Message = {
                role: 'assistant',
                content: `Document processed successfully: ${file.name}. You can now ask questions about it!`,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, successMessage]);
        } catch (error: any) {
            console.error('Upload error details:', {
                message: error.message,
                response: error.response?.data,
                status: error.response?.status
            });

            let errorMsg = 'Error uploading document: ';
            if (error.code === 'ECONNABORTED') {
                errorMsg += 'Request timed out. The file might be too large or the server is busy.';
            } else if (error.response?.data?.detail) {
                errorMsg += error.response.data.detail;
            } else {
                errorMsg += error.message || 'Unknown error occurred';
            }

            const errorMessage: Message = {
                role: 'assistant',
                content: errorMsg,
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
            {/* Messages Container */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.map((message, index) => (
                    <div
                        key={index}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                        <div
                            className={`max-w-[80%] rounded-lg p-4 ${message.role === 'user'
                                ? 'bg-primary-600 text-white'
                                : 'bg-white shadow-md text-gray-800'
                                }`}
                        >
                            <p className="text-sm">{message.content}</p>
                            <p className="text-xs mt-1 opacity-75">
                                {message.timestamp.toLocaleTimeString()}
                            </p>
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-white shadow-md text-gray-800 rounded-lg p-4">
                            <div className="flex items-center space-x-2">
                                <div className="animate-pulse">Thinking</div>
                                <div className="flex space-x-1">
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Container */}
            <div className="border-t bg-white p-4 space-y-4">
                <div className="flex justify-center">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        accept=".pdf,.txt,.md,.html"
                        className="file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 
                     file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 
                     hover:file:bg-primary-100 cursor-pointer"
                    />
                </div>

                <form onSubmit={handleSend} className="flex space-x-4">
                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder="Ask a question about your documents..."
                        className="flex-1 p-3 border rounded-lg focus:outline-none focus:ring-2 
                     focus:ring-primary-500 focus:border-primary-500"
                        disabled={isLoading}
                    />
                    <button
                        type="submit"
                        disabled={isLoading || !input.trim()}
                        className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 
                     disabled:opacity-50 disabled:cursor-not-allowed transition-colors
                     duration-200"
                    >
                        Send
                    </button>
                </form>
            </div>
        </div>
    );
};

export default Chat; 