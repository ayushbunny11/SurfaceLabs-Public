import { useEffect, useState, useContext, useRef } from "react";
import { AppContext } from "../../context/AppContext";
import { AppView } from "../../types";
import { TerminalWindow } from "./TerminalWindow";
import { github_analysis_stream } from "../../configs/api_config";
import { streamSSE } from "../../utils/sse";

type LogType = "info" | "success" | "process" | "error" | "warning";

interface LogEntry {
  id?: string;
  message: string;
  timestamp: string;
  type: LogType;
}

const AnalysisView = () => {
  const { setView, repoData } = useContext(AppContext);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [status, setStatus] = useState<"processing" | "success" | "failure">("processing");
  const hasStartedRef = useRef(false);

  const addLog = (message: string, type: LogType = "process", id?: string) => {
    const now = new Date();
    const timeString = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
    
    setLogs((prev) => {
        if (id) {
            const existingIndex = prev.findIndex(log => log.id === id);
            if (existingIndex !== -1) {
                const newLogs = [...prev];
                newLogs[existingIndex] = { ...newLogs[existingIndex], message, type, timestamp: timeString };
                return newLogs;
            }
        }
        return [...prev, { id, message, timestamp: timeString, type }];
    });
  };

  useEffect(() => {
    console.log("[AnalysisView] Effect Triggered", { 
        hasStarted: hasStartedRef.current, 
        repoDataPresent: !!repoData,
        cloneId: repoData?.cloneId 
    });

    if (hasStartedRef.current) return;

    if (!repoData?.cloneId) {
       console.log("[AnalysisView] Waiting for cloneId...");
       // Don't mark as started yet, wait for data
       return;
    }
    
    console.log("[AnalysisView] Starting analysis stream...", repoData.cloneId);
    hasStartedRef.current = true;

    const startAnalysisStream = async () => {
      try {
        addLog(`Initializing analysis for ${repoData.name}...`, "info");

        await streamSSE(
          github_analysis_stream,
          { folder_ids: [repoData.cloneId] },
          {
            onError: (errorMsg) => {
               addLog(`Error: ${errorMsg}`, "error");
               setStatus("failure");
            },
            onEvent: (eventType, data) => {
               // Handle specific events
               const chunkId = data.chunk_index !== undefined ? `chunk-${data.chunk_index}` : undefined;
               
               if (eventType === "progress") {
                   addLog(data.message, "process", chunkId);
               }
               else if (eventType === "chunk_complete") {
                   addLog(data.message, "success", chunkId);
               } 
               else if (eventType === "chunk_failed") {
                   addLog(`✗ ${data.message}`, "warning", chunkId);
               } 
               else if (eventType === "complete") {
                   if (data.status === "success") {
                       addLog("Analysis completed successfully.", "success");
                       setStatus("success");
                   } else {
                       addLog(`Analysis completed with issues: ${data.message}`, "warning");
                       setStatus("success");
                   }
               }
            }
          }
        );

      } catch (error: any) {
        console.error("Analysis stream failed:", error);
        // streamSSE throws on error, so we catch it here to update UI if onError didn't already
        if (status !== "failure") {
             addLog(`Connection failed: ${error.message}`, "error");
             setStatus("failure");
        }
      }
    };

    startAnalysisStream();

  }, [repoData]);

  const handleProceed = () => {
    setView(AppView.WORKSPACE);
  };

  const handleAbort = () => {
    setView(AppView.LANDING);
  };

  return (
    <TerminalWindow 
        logs={logs}
        completed={status !== "processing"}
        status={status}
        repoData={repoData}
        onProceed={handleProceed}
        onAbort={handleAbort}
    />
  );
};

export default AnalysisView;
