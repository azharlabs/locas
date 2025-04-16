import React from 'react';

const TypingIndicator: React.FC = () => {
  return (
    <div className="py-2">
      <div className="flex justify-start">
        <div className="max-w-3xl py-3 px-5 text-gray-800 w-full">
          <div className="animate-pulse space-y-2">
            <div className="h-2 bg-gray-200 rounded w-3/4"></div>
            <div className="h-2 bg-gray-200 rounded w-1/2"></div>
            <div className="h-2 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;