import React from 'react';
import ReactMarkdown from 'react-markdown';

interface Message {
  text: string;  sender: 'user' | 'assistant';
  tool: string | null;
}

type ChatMessageProps = {
  message: Message;
};

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { text, sender, tool } = message;

  return (
    <div className="py-2">
      {sender === 'user' ? (
         <div className="flex justify-end">
          <div className="max-w-3xl rounded-lg bg-primary-50 py-3 px-5 text-gray-800 border border-primary-100">
            <p className="whitespace-pre-wrap text-sm">{text}</p>
          </div>
         
        </div>
      ) : (
        <div className="flex justify-start">
          <div className="max-w-3xl py-3 px-5 text-gray-800">
            <ReactMarkdown className="markdown text-sm">
              {text}
            </ReactMarkdown>
            {tool && (
              <div className="text-xs text-gray-500 mt-1 ml-2">
                Tool: {tool}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;