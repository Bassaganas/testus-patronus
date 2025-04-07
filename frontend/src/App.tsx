import React from 'react';
import Chat from './components/Chat';

function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto py-4 px-4">
          <h1 className="text-2xl font-bold text-gray-900">Testus Patronus</h1>
          <p className="text-sm text-gray-500">RAG-based Educational Assistant</p>
        </div>
      </header>
      <main className="max-w-4xl mx-auto py-4">
        <Chat />
      </main>
    </div>
  );
}

export default App;
