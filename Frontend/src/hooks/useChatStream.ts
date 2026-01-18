import { useState, useCallback, useRef } from "react";
import { streamSSE } from "../utils/sse";
import { chat_api_stream } from "../configs/api_config";
import type { Message } from "../types";

export const useChatStream = () => {
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Reference to the current session ID
  const sessionIdRef = useRef<string | null>(null);

  const sendMessage = useCallback(async (
    query: string,
    onUpdate: (update: Partial<Message>) => void,
    folderId: string = "3000ffa4303f4d1fb92a60b107462df2",
    userId: string = "918262"
  ) => {
    setIsStreaming(true);
    setError(null);

    // Initial message state
    let currentStatus = "Initializing...";
    const history: string[] = [];
    let content = "";
    const citations: { title: string; uri: string; type: string }[] = [];
    const stateChanges: string[] = [];

    // Helper to build reasoning string (current status + history)
    const buildReasoning = () => {
      // Format: Current status on top, history below (separated by special marker)
      if (history.length === 0) {
        return currentStatus;
      }
      return `${currentStatus}\n---\n${history.join("\n")}`;
    };

    // Immediately show the initialization message
    onUpdate({ reasoning: buildReasoning(), isThinking: true });


    try {
      console.log(`[useChatStream] Sending with session_id: ${sessionIdRef.current || 'NEW SESSION'}`);
      
      await streamSSE(chat_api_stream, {
        query,
        user_id: userId,
        session_id: sessionIdRef.current,
        folder_id: folderId
      }, {
        onHeaders: (headers) => {
          const newSessionId = headers.get("X-Chat-Session-Id");
          if (newSessionId) {
            console.log(`[useChatStream] Received session_id: ${newSessionId}`);
            sessionIdRef.current = newSessionId;
          }
        },
        onEvent: (event, data) => {
          console.log(`[useChatStream] Event: ${event}`, data);

          switch (event) {
            case "status":
              // Move previous status to history if it's meaningful
              if (currentStatus && currentStatus !== "Initializing..." && !history.includes(currentStatus)) {
                history.push(currentStatus);
              }
              currentStatus = data.status;
              break;

            case "tool_call":
            case "tool call":
              // Skip - status already shows this
              break;

            case "tool_response":
            case "tool response":
              // Append result to current status
              const summary = data.response_summary || "Done";
              currentStatus = `${data.tool_name} - ${summary}`;
              break;

            case "sub_agent_call":
            case "sub_agent call":
            case "sub agent call":
              // Skip - status already shows delegation
              break;

            case "sub_agent_response":
            case "sub_agent response":
            case "sub agent response":
              // Append result to current status
              const agentSummary = data.response_summary || "Complete";
              currentStatus = `${data.tool_name} - ${agentSummary}`;
              break;
            
            case "token":
              content += (data.token || "");
              break;
            
            case "citation":
              if (data.citation) {
                citations.push(data.citation);
              }
              break;
            
            case "state_change":
            case "state change":
              if (data.state_delta) {
                stateChanges.push(data.state_delta);
              }
              break;
            
            case "complete":
              setIsStreaming(false);
              // Final update with thinking stopped
              onUpdate({ 
                reasoning: buildReasoning(), 
                content, 
                isThinking: false,
                citations: [...citations],
                stateChanges: [...stateChanges]
              });
              return; // Exit early, no more updates needed
            
            case "error":
              const errorMsg = data.message || "An error occurred";
              setError(errorMsg);
              setIsStreaming(false);
              // Show error in UI and stop thinking
              currentStatus = `Error: ${errorMsg}`;
              onUpdate({ 
                reasoning: buildReasoning(), 
                content: content || `Sorry, an error occurred: ${errorMsg}`, 
                isThinking: false,
                citations: [...citations],
                stateChanges: [...stateChanges]
              });
              return; // Exit early
            
            default:
              break;
          }

          // Update UI
          const stillThinking = content.length === 0;
          onUpdate({ 
              reasoning: buildReasoning(), 
              content, 
              isThinking: stillThinking,
              citations: [...citations],
              stateChanges: [...stateChanges]
          });
        },
        onError: (err) => {
          setError(err);
          setIsStreaming(false);
          // Show error in UI
          currentStatus = `Error: ${err}`;
          onUpdate({ 
            reasoning: buildReasoning(), 
            content: `Sorry, an error occurred: ${err}`, 
            isThinking: false,
            citations: [...citations],
            stateChanges: [...stateChanges]
          });
        }
      });
    } catch (err: any) {
      const errorMsg = err.message || "Stream connection failed";
      setError(errorMsg);
      setIsStreaming(false);
      onUpdate({ 
        reasoning: `Error: ${errorMsg}`, 
        content: `Sorry, an error occurred: ${errorMsg}`, 
        isThinking: false
      });
    }
  }, []);

  const resetSession = useCallback(() => {
    sessionIdRef.current = null;
  }, []);

  return {
    sendMessage,
    isStreaming,
    error,
    resetSession,
    sessionId: sessionIdRef.current
  };
};
