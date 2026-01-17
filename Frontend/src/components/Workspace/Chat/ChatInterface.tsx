import { type FC, useState } from "react";
import { Send } from "@mui/icons-material";
import { IconButton } from "@mui/material";
import { Messages } from "./Messages";

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  reasoning?: string;
}

interface ChatInterfaceProps {
  messages: Message[];
  onSend: (message: string) => void;
}

export const ChatInterface: FC<ChatInterfaceProps> = ({ messages, onSend }) => {
  const [input, setInput] = useState("");

  const handleSendClick = () => {
    if (input.trim()) {
      onSend(input);
      setInput("");
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0c0c0c] border-l border-neutral-800 text-neutral-200 font-sans">
      {/* Messages */}
      <Messages messages={messages} />

      {/* Input Area */}
      <div className="p-4 border-t border-neutral-800 bg-[#0c0c0c]">
        <div className="max-w-3xl mx-auto relative flex items-end gap-2 bg-[#18181b] border border-neutral-800 rounded-xl p-2 focus-within:ring-1 focus-within:ring-neutral-700 transition-all shadow-sm">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendClick();
              }
            }}
            placeholder="Describe your feature requirements..."
            className="w-full bg-transparent text-sm text-neutral-200 placeholder:text-neutral-600 resize-none max-h-32 min-h-[44px] p-2.5 focus:outline-none scrollbar-none"
            rows={1}
          />
          <div className="pb-1 pr-1">
            <IconButton
              onClick={handleSendClick}
              disabled={!input.trim()}
              sx={{
                backgroundColor: input.trim() ? "white" : "#262626",
                color: input.trim() ? "black" : "#525252",
                width: 32,
                height: 32,
                "&:hover": {
                  backgroundColor: input.trim() ? "#e5e5e5" : "#262626",
                },
                transition: "all 0.2s",
              }}
            >
              <Send sx={{ fontSize: 16 }} />
            </IconButton>
          </div>
        </div>
      </div>
    </div>
  );
};
