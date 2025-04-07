import React from 'react';
import './App.css';
import Chat from './components/Chat';

function App() {
    return (
        <div className="App">
            <header className="App-header">
                <h1 className="text-3xl font-bold mb-2">Testus Patronus</h1>
                <p className="text-lg mb-4">RAG-based Educational Assistant</p>
            </header>
            <main className="bg-gray-50 flex-1">
                <Chat />
            </main>
        </div>
    );
}

export default App;
