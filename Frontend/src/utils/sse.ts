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
      throw new Error(`Failed to connect to server: ${response.statusText}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error("No response stream available");
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const text = decoder.decode(value);
      const lines = text.split("\n");

      for (const line of lines) {
        if (line.startsWith("event:")) {
          continue;
        }

        if (line.startsWith("data:")) {
          const jsonStr = line.substring(5).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);

            // Generic event handler
            if (callbacks.onEvent) {
              callbacks.onEvent(data.event || "unknown", data);
            }

            // Specific event handlers based on the convention we established
            if (data.event === "progress") {
              callbacks.onProgress?.(data.percent || 0, data.message || "");
            } else if (
              data.event === "metadata" ||
              (!data.event && data.owner)
            ) {
              callbacks.onMetadata?.(data);
            } else if (data.event === "complete") {
              callbacks.onComplete?.(data.data);
            } else if (data.event === "error") {
              const msg = data.message || "An error occurred";
              callbacks.onError?.(msg);
              // We don't throw here to allow the caller to decide, 
              // but generic loop might continue unless we return or throw?
              // Usually error event in SSE means stream might stop or we should stop.
              // For now, let's throw to break the loop in the catch block 
              // but we need to pass this up. 
              throw new Error(msg);
            }
          } catch (parseErr: any) {
            // Re-throw (to break loop) if it's the error we just threw above
            if (parseErr.message && !parseErr.message.includes("JSON")) {
              throw parseErr;
            }
          }
        }
      }
    }
  } catch (err: any) {
    let errorMessage = err.message || "Unknown error";

    if (errorMessage.includes("Failed to fetch") || errorMessage.includes("NetworkError")) {
      errorMessage = "Network error. Please check your connection.";
    } else if (errorMessage.includes("connect")) {
      errorMessage = "Cannot connect to server. Ensure backend is running.";
    }
    
    callbacks.onError?.(errorMessage);
    throw new Error(errorMessage);
  }
};
