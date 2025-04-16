import React from 'react';
import ReactMarkdown from 'react-markdown';

type ChatMessageProps = {
  message: {
    text: string;
    sender: 'user' | 'assistant';
  };
};

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { text, sender } = message;
  const isUser = sender === 'user';

  return (
    <div className="py-2">
      {isUser ? (
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
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatMessage;