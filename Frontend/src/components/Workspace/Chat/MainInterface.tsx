import { ChatInterface } from "./ChatInterface";
import type { Message } from "./ChatInterface";
import { CodeViewer } from "../Code/CodeViewer";
import { Menu, PlayArrow, Commit } from "@mui/icons-material";
import { IconButton, Button } from "@mui/material";
import { useState, type FC } from "react";

interface MainInterfaceProps {
    onToggleSidebar: () => void;
}

export const MainInterface: FC<MainInterfaceProps> = ({ onToggleSidebar }) => {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleSend = (input: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, newMessage]);

    // Simulate AI response (Mock for now) with reference features
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "assistant",
          content:
            "I've drafted a plan to integrate the new payment provider. \n\n**Integration Plan:**\n1.  Create `PaymentService` interface.\n2.  Implement `StripeAdapter` class.\n3.  Update `CheckoutController` to use the new service.",
          timestamp: new Date().toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          }),
          reasoning:
            "Detected 'Stripe' keyword. Located `src/services/payment`. Identified missing Adapter pattern implementation. Checking `package.json` for `@stripe/stripe-js` dependency.",
        },
      ]);
    }, 1500);
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
            <span>REQIO-IQ</span>
            <span className="text-neutral-700">/</span>
            <span className="text-neutral-300">Workspace</span>
          </div>
        </div>

        {/* Right Actions */}
        <div className="flex items-center gap-3">
          <Button
            variant="outlined"
            size="small"
            startIcon={<PlayArrow sx={{ fontSize: 16 }} />}
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
            Run Tests
          </Button>
          <Button
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
          </Button>
        </div>
      </header>

      {/* Main Content (Split View Placeholders) */}
      <div className="flex-1 flex overflow-hidden">
        <CodeViewer />
        <div className="w-[400px] border-l border-neutral-800 flex flex-col">
          <ChatInterface messages={messages} onSend={handleSend} />
        </div>
      </div>
    </div>
  );
};
