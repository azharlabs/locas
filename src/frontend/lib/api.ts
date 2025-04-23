const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

interface ProcessQueryResponse {
  status: 'success' | 'error';
  result?: string;
  message?: string;
  tool?: string;
}
async function processQuery(queryText: string, userId: string | undefined): Promise<ProcessQueryResponse> {
  const response = await fetch(`${API_URL}/api/process-query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: queryText, userId: userId }),
  });
  return (await response.json()) as ProcessQueryResponse;
}

// Event type for streaming process query events
export interface ProcessQueryStreamEvent {
  type: 'tool' | 'final';
  tool?: string;
  result?: string;
  status?: 'success' | 'error' | 'warning';
  message?: string;
}

/**
 * Stream processing of a location-based query via Server-Sent Events.
 * onEvent will be called for each event: tool usage and final result.
 */
async function processQueryStream(
  queryText: string,
  userId: string | undefined,
  onEvent: (event: ProcessQueryStreamEvent) => void
): Promise<void> {
  const response = await fetch(`${API_URL}/api/process-query-stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: queryText, userId: userId }),
  });
  if (!response.body) {
    throw new Error('No response body');
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split('\n\n');
    buffer = parts.pop()!;
    for (const part of parts) {
      const trimmed = part.trim();
      if (!trimmed.startsWith('data:')) continue;
      const jsonStr = trimmed.slice('data:'.length).trim();
      let event: ProcessQueryStreamEvent;
      try {
        event = JSON.parse(jsonStr);
      } catch (e) {
        console.error('Error parsing stream event:', e);
        continue;
      }
      onEvent(event);
    }
  }
}

export { processQuery, processQueryStream };