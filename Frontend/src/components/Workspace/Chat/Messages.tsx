import { type FC, useRef, useEffect, useState } from "react";
import {
  SmartToy,
  Person,
  Lightbulb,
  ExpandMore,
  ExpandLess,
  Description,
  Add,
} from "@mui/icons-material";
import { motion, AnimatePresence } from "framer-motion";
import type { Message } from "./ChatInterface";

interface MessagesProps {
  messages: Message[];
}

export const Messages: FC<MessagesProps> = ({ messages }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto p-4 space-y-6 scrollbar-thin scrollbar-thumb-neutral-800"
    >
      {messages.length === 0 && (
        <div className="h-full flex flex-col items-center justify-center text-neutral-500 opacity-60">
          <div className="w-16 h-16 rounded-2xl bg-neutral-900 border border-neutral-800 flex items-center justify-center mb-6">
            <Add sx={{ fontSize: 32, opacity: 0.5 }} />
          </div>
          <h3 className="text-lg font-medium text-neutral-300 mb-2">
            Start a New Feature
          </h3>
          <p className="max-w-xs text-center text-sm leading-relaxed">
            Describe your feature requirements. I'll analyze the architecture
            and generate the necessary code.
          </p>
        </div>
      )}

      <AnimatePresence initial={false}>
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 max-w-3xl mx-auto w-full ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-lg bg-[#1e1e24] border border-[#2d2d3b] flex items-center justify-center shrink-0 mt-1">
                <SmartToy sx={{ fontSize: 16, color: "#818cf8" }} />
              </div>
            )}

            <div
              className={`max-w-[85%] flex flex-col ${msg.role === "user" ? "items-end" : "items-start w-full"}`}
            >
              {/* Reasoning Accordion */}
              {msg.reasoning && (
                <ReasoningDisclosure reasoning={msg.reasoning} />
              )}

              <div
                className={`px-5 py-3.5 rounded-2xl text-sm leading-7 shadow-sm ${
                  msg.role === "user"
                    ? "bg-neutral-800 text-white rounded-br-none border border-neutral-700"
                    : "bg-[#111111] text-neutral-300 border border-neutral-800 rounded-bl-none w-full"
                }`}
              >
                <div className="whitespace-pre-wrap">{msg.content}</div>

                {/* Mock Proposed Changes (Only for AI) - Hardcoded for demo fidelity */}
                {msg.role === "assistant" &&
                  msg.content.includes("Proposed Changes") && (
                    <div className="mt-6 space-y-3">
                      <div className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">
                        Proposed Changes
                      </div>
                      <div className="bg-[#050505] rounded-lg border border-neutral-800 overflow-hidden">
                        <div className="flex items-center justify-between px-3 py-2 bg-neutral-900/50 border-b border-neutral-800">
                          <div className="flex items-center gap-2">
                            <Description
                              sx={{ fontSize: 14, color: "#fbbf24" }}
                            />
                            <span className="font-mono text-xs text-neutral-300">
                              src/adapters/StripeAdapter.ts
                            </span>
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-green-900/20 text-green-500 border border-green-900/30">
                              NEW
                            </span>
                          </div>
                        </div>
                        <div className="p-3 font-mono text-xs text-neutral-400">
                          // Mock diff content would go here...
                        </div>
                      </div>
                    </div>
                  )}
              </div>
              <span className="text-[10px] text-neutral-600 mt-1 px-1">
                {msg.timestamp}
              </span>
            </div>

            {msg.role === "user" && (
              <div className="w-8 h-8 rounded-lg bg-neutral-800 border border-neutral-700 flex items-center justify-center shrink-0 mt-1">
                <Person sx={{ fontSize: 16, color: "rgb(163 163 163)" }} />
              </div>
            )}
          </motion.div>
        ))}
      </AnimatePresence>
    </div>
  );
};

// Reasoning Component
const ReasoningDisclosure: FC<{ reasoning: string }> = ({ reasoning }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="mb-2 self-start">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-xs font-medium text-neutral-500 hover:text-indigo-400 transition-colors select-none bg-neutral-900 border border-neutral-800 px-3 py-1.5 rounded-full hover:border-neutral-700"
      >
        <Lightbulb
          sx={{ fontSize: 14 }}
          className={isOpen ? "text-indigo-400" : ""}
        />
        {isOpen ? "Hide reasoning" : "View analysis process"}
        {isOpen ? (
          <ExpandLess sx={{ fontSize: 14 }} />
        ) : (
          <ExpandMore sx={{ fontSize: 14 }} />
        )}
      </button>
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="mt-2 pl-4 border-l-2 border-neutral-800 py-2 ml-2">
              <p className="text-xs text-neutral-400 font-mono leading-5 tracking-tight max-w-prose">
                {reasoning}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
