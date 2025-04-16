const API_URL = process.env.NEXT_PUBLIC_BACKEND_URL;

async function processQuery(queryText: string, userId: string | undefined): Promise<any> {
  const response = await fetch(`${API_URL}/api/process-query`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: queryText, userId: userId }),
  });
  return await response.json();
  }
  export { processQuery }