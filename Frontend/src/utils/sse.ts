export interface SSEEvent<T = any> {
  event: string;
  data: T;
}

export interface SSECallbacks {
  onProgress?: (percent: number, message: string) => void;
  onMetadata?: (data: any) => void;
  onComplete?: (data: any) => void;
  onError?: (error: string) => void;
  onEvent?: (event: string, data: any) => void;
  onHeaders?: (headers: Headers) => void;
}

export const streamSSE = async (
  endpoint: string,
  body: any,
  callbacks: SSECallbacks
) => {
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text().catch(() => response.statusText);
      throw new Error(`Failed to connect to server: ${errorText}`);
    }

    // Call onHeaders if provided (for session ID extraction, etc.)
    if (callbacks.onHeaders) {
      callbacks.onHeaders(response.headers);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error("No response stream available");
    }

    let lastEventType = "message";
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      
      const parts = buffer.split("\n");
      // Keep the last partial line in the buffer
      buffer = parts.pop() || "";

      for (const part of parts) {
        const line = part.trim();
        if (!line) continue;

        if (line.startsWith("event:")) {
          lastEventType = line.substring(6).trim();
          // console.log(`[SSE Parser] Event: ${lastEventType}`);
        } else if (line.startsWith("data:")) {
          const jsonStr = line.substring(5).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);
            // console.log(`[SSE Parser] Data:`, data);

            // Generic event handler
            callbacks.onEvent?.(lastEventType, data);

            // Specific event handlers for backward compatibility
            const eventType = lastEventType !== "message" ? lastEventType : data.event;
            
            if (eventType === "progress") {
              callbacks.onProgress?.(data.percent || 0, data.message || "");
            } else if (eventType === "metadata" || (!eventType && data.owner)) {
              callbacks.onMetadata?.(data);
            } else if (eventType === "complete") {
              callbacks.onComplete?.(data);
            } else if (eventType === "error") {
              const msg = data.message || "An error occurred";
              callbacks.onError?.(msg);
              throw new Error(msg);
            }
          } catch (parseErr: any) {
            if (lastEventType === "error") throw parseErr;
            console.error("SSE JSON parse error:", parseErr, "Line:", line);
          }
        }
      }
    }
  } catch (err: any) {
    let errorMessage = err.message || "Unknown error";

    if (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError")) {
      errorMessage = "Network error. Please check your connection.";
    }
    
    callbacks.onError?.(errorMessage);
    throw new Error(errorMessage);
  }
};
