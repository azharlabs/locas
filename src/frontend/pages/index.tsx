import { useState, useRef, useEffect, useCallback } from "react";
import { useSession } from "next-auth/react";
import Layout from "../components/Layout";
import ChatMessage from "../components/ChatMessage";
import ChatInput from "../components/ChatInput";
import TypingIndicator from "../components/TypingIndicator";
import { processQueryStream } from "../lib/api";
import { FaLock } from "react-icons/fa";

type Message = {
  text: string;
  tool: string | null;
  sender: 'user' | 'assistant';
};

export default function Home() {
  const { data: session } = useSession();
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentTool, setCurrentTool] = useState<string>("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
    

  const handleSendMessage = useCallback(
    async (text: string) => {
      // Add user message
      const userMessage: Message = { text, sender: "user", tool: null }; // Set tool to null for user messages
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setCurrentTool("");
      try {
        // Stream the query process
        await processQueryStream(text, session?.user?.id, (event) => {
          if (event.type === 'tool') {
            // Update current tool while loading
            setCurrentTool(event.tool || '');
          } else if (event.type === 'final') {
            // Final result received
            if (event.status === 'success') {
              const assistantMessage: Message = {
                text: event.result || '',
                sender: 'assistant',
                tool: event.tool || null,
              };
              setMessages((prev) => [...prev, assistantMessage]);
            } else {
              const errorMessage: Message = {
                text:
                  event.message ||
                  'Sorry, there was an error processing your query.',
                sender: 'assistant',
                tool: null,
              };
              setMessages((prev) => [...prev, errorMessage]);
            }
          }
        });
      } catch (error) {
        console.error('Error sending message:', error);
        const errorMessage: Message = {
          text:
            'Sorry, there was an error connecting to the server. Please try again later.',
          sender: 'assistant',
          tool: null,
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
        setCurrentTool('');
      }
    }, [session?.user?.id]
  );

  return (
    <Layout>
      <div className="mx-0 sm:mx-12 md:mx-24 lg:mx-48 xl:mx-64 h-full">
        <div className="flex h-full flex-col bg-white overflow-hidden">
          <div className="flex-1 overflow-y-auto px-5 py-4">
            {messages.map((message, index) => (
                <ChatMessage key={index} message={message} />
              ))
            }
            {isLoading && (
              <div className="flex flex-col">
                {currentTool && (
                  <span className="mb-1 text-sm italic text-gray-500">
                    Using: {currentTool}
                  </span>
                )}
                <TypingIndicator /></div>)}
            <div ref={messagesEndRef} />
          </div>

          {session ? (
            <ChatInput onSendMessage={handleSendMessage} isLoading={isLoading} />
          ) : (
            <div className="p-4 text-center">
              <p className="text-gray-600">Please sign in to use the Locas</p>
            </div>
          )}
        </div>
      </div>
    </Layout>
  );
}
