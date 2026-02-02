import { ChatInterface } from "./ChatInterface";
import { CodeViewer } from "../Code/CodeViewer";
import { Menu, Download } from "@mui/icons-material";
import { IconButton, Button } from "@mui/material";
import { useState, type FC, useContext, useCallback, useEffect } from "react";
import { AppContext } from "../../../context/AppContext";
import { useChatStream } from "../../../hooks/useChatStream";
import type { Message } from "../../../types";
import { downloadFile } from "../../../services/api";
import { CircularProgress } from "@mui/material";

interface MainInterfaceProps {
    onToggleSidebar: () => void;
}

export const MainInterface: FC<MainInterfaceProps> = ({ onToggleSidebar }) => {
  const { repoData, activeFile, setSessionUsage } = useContext(AppContext);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const { sendMessage, isStreaming } = useChatStream();

  // Calculate and update session usage whenever messages change
  useEffect(() => {
    const totalUsage = messages.reduce(
      (acc, msg) => {
        if (msg.usage) {
          acc.prompt_tokens += msg.usage.prompt_tokens || 0;
          acc.candidates_tokens += msg.usage.candidates_tokens || 0;
          acc.cached_tokens += msg.usage.cached_tokens || 0;
          acc.total_tokens += msg.usage.total_tokens || 0;
        }
        return acc;
      },
      { prompt_tokens: 0, candidates_tokens: 0, cached_tokens: 0, total_tokens: 0 }
    );
    setSessionUsage(totalUsage);
  }, [messages, setSessionUsage]);

  const handleSend = useCallback(async (input: string) => {
    if (!input.trim() || isStreaming) return;
    
    if (!repoData?.cloneId) {
      console.error("Missing repo cloneId, cannot send message");
      return;
    }

    // 1. Build query with file context if a file is open
    let queryWithContext = input;
    if (activeFile?.path) {
      queryWithContext = `[Context: User is currently viewing file "${activeFile.path}"]\n\n${input}`;
    }

    // 2. Generate unique IDs for this exchange
    const userId = crypto.randomUUID();
    const assistantId = crypto.randomUUID();

    const userMessage: Message = {
      id: userId,
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const placeholderAssistant: Message = {
      id: assistantId,
      role: "assistant",
      content: "",
      reasoning: "Preparing...",
      isThinking: true,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage, placeholderAssistant]);

    // 3. Start Streaming
    await sendMessage(
      queryWithContext,
      (update: Partial<Message>) => {
        setMessages((prev) => 
          prev.map((msg) => 
            msg.id === assistantId ? { ...msg, ...update } : msg
          )
        );
      },
      repoData.cloneId
    );
  }, [repoData, activeFile, sendMessage, isStreaming]);

  const handleDownload = async () => {
    if (!repoData?.cloneId) {
        console.warn("No repo cloned to download");
        return;
    }
    
    try {
        setIsDownloading(true);
        await downloadFile("/features/download/repo", { folder_id: repoData.cloneId });
        window.dispatchEvent(new CustomEvent('SHOW_SNACKBAR', { 
            detail: { message: "Download started", severity: 'info' } 
        }));
    } catch (error) {
        console.error("Download failed", error);
        window.dispatchEvent(new CustomEvent('SHOW_SNACKBAR', { 
            detail: { message: "Failed to download repository", severity: 'error' } 
        }));
    } finally {
        setIsDownloading(false);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-[#0c0c0c]">
      {/* Header / Toolbar */}
      <header className="h-14 border-b border-neutral-800 flex items-center px-4 justify-between bg-[#0c0c0c] z-10">
        <div className="flex items-center gap-3">
          <IconButton
            onClick={onToggleSidebar}
            sx={{ color: "rgb(163 163 163)" }}
            size="small"
          >
            <Menu fontSize="small" />
          </IconButton>
          <div className="h-4 w-px bg-neutral-800 mx-1" />
          <div className="flex items-center gap-2 text-sm text-neutral-500">
            <span>SurfaceLabs</span>
            <span className="text-neutral-700">/</span>
            <span className="text-neutral-300">Workspace</span>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <Button
            variant="outlined"
            size="small"
            onClick={handleDownload}
            startIcon={<Download sx={{ fontSize: 16 }} />}
            sx={{
               borderColor: "#404040",
               color: "#a3a3a3",
               textTransform: "none",
               fontSize: "0.75rem",
               minWidth: "auto",
               px: 1.5,
               py: 0.5,
               "&:hover": {
                  borderColor: "#a3a3a3",
                  color: "#e5e5e5",
                  backgroundColor: "rgba(255, 255, 255, 0.05)"
               }
            }}
          >
            {isDownloading ? <CircularProgress size={16} sx={{ color: "inherit", mr: 1 }} /> : null}
            {isDownloading ? "Downloading..." : "Download Zip"}
          </Button>
          {/* <Button
            variant="contained"
            size="small"
            startIcon={<Commit sx={{ fontSize: 16 }} />}
            sx={{
               backgroundColor: "#f5f5f5",
               color: "#171717",
               textTransform: "none",
               fontSize: "0.75rem",
               minWidth: "auto",
               px: 1.5,
               py: 0.5,
               "&:hover": {
                  backgroundColor: "#ffffff"
               }
            }}
          >
            Create PR
          </Button> */}
        </div>
      </header>

      {/* Main Content (Split View Placeholders) */}
      <div className="flex-1 flex overflow-hidden">
        <CodeViewer />
        <div className="w-[460px] border-l border-neutral-800 flex flex-col">
          <ChatInterface messages={messages} onSend={handleSend} isLoading={isStreaming} />
        </div>
      </div>
    </div>
  );
};
