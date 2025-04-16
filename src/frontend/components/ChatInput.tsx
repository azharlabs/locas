import React, { useState } from 'react';
import { FaPaperPlane } from 'react-icons/fa';

type ChatInputProps = {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
};

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isLoading }) => {
  const [message, setMessage] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSendMessage(message);
      setMessage('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex-shrink-0 bg-white px-5 py-4 border-t border-gray-100">
      <div className="relative flex items-center">
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter your location query..."
          className="input pr-12 text-sm"
          disabled={isLoading}
        />
        <button
          type="submit"
          className="absolute right-2 rounded-full p-2 text-primary-600 hover:bg-gray-100 disabled:opacity-50"
          disabled={!message.trim() || isLoading}
        >
          <FaPaperPlane />
        </button>
      </div>
      <div className="mt-2 text-xs text-gray-500">
        <p>Try: &quot;Can I buy land at 40.7128, -74.0060?&quot; or &quot;Are there any hospitals near Times Square, New York?&quot;</p>
      </div>
    </form>
  );
};

export default ChatInput;