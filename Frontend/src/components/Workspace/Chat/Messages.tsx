import { type FC, useRef, useEffect, useState } from "react";
import {
  SmartToy,
  Person,
  ExpandMore,
  ExpandLess,
  Description,
  Add,
} from "@mui/icons-material";
import { motion, AnimatePresence } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import "./MarkdownStyles.css";
import type { Message } from "../../../types";

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
              <div
                className={`px-5 py-3.5 rounded-2xl text-sm leading-7 shadow-sm overflow-hidden ${
                  msg.role === "user"
                    ? "bg-neutral-800 text-white rounded-br-none border border-neutral-700"
                    : "bg-[#111111] text-neutral-300 border border-neutral-800 rounded-bl-none w-full"
                }`}
              >
                {/* Reasoning Accordion (Inside bubble for Assistant) */}
                {msg.role === "assistant" &&
                  (msg.reasoning || msg.isThinking) && (
                    <ReasoningDisclosure
                      reasoning={msg.reasoning || ""}
                      isThinking={msg.isThinking}
                    />
                  )}

                {msg.role === "assistant" && msg.isThinking && !msg.content && (
                  <div className="flex items-center gap-1.5 py-1">
                    <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
                    <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse [animation-delay:200ms]" />
                    <span className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse [animation-delay:400ms]" />
                  </div>
                )}

                <div className="markdown-content">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ node, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || "");
                        const isInline =
                          !match && !String(children).includes("\n");
                        // Exclude ref from props to avoid type errors with SyntaxHighlighter
                        const { ref, ...rest } = props as any;
                        return !isInline && match ? (
                          <div className="code-block-wrapper">
                            <div className="code-block-header">
                              <span className="code-block-lang">
                                {match[1]}
                              </span>
                            </div>
                            <SyntaxHighlighter
                              style={vscDarkPlus as any}
                              language={match[1]}
                              PreTag="div"
                              customStyle={{
                                margin: 0,
                                padding: "1rem",
                                background: "transparent",
                                fontSize: "13px",
                              }}
                              wrapLongLines={true}
                              {...rest}
                            >
                              {String(children).replace(/\n$/, "")}
                            </SyntaxHighlighter>
                          </div>
                        ) : (
                          <code {...props}>{children}</code>
                        );
                      },
                      a: ({ href, children }) => (
                        <a
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {children}
                        </a>
                      ),
                    }}
                  >
                    {msg.content}
                  </ReactMarkdown>
                </div>

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
              <span className="text-[10px] text-neutral-600 mt-1 px-1 flex items-center justify-between w-full">
                <span>{msg.timestamp}</span>
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

// Reasoning Component - Shows current status prominently, history expandable
const ReasoningDisclosure: FC<{ reasoning: string; isThinking?: boolean }> = ({
  reasoning,
  isThinking,
}) => {
  const [showHistory, setShowHistory] = useState(false);

  // Parse reasoning: "current\n---\nhistory line 1\nhistory line 2"
  const parts = reasoning.split("\n---\n");
  const currentStatus = parts[0] || "";
  const historyLines = parts[1]
    ? parts[1].split("\n").filter((line) => line.trim())
    : [];

  return (
    <div className="mb-3 w-full">
      {/* Current Status - Always visible when thinking */}
      <div className="flex items-center gap-2 text-xs text-neutral-400 px-1 py-1.5">
        {isThinking && (
          <div className="w-2.5 h-2.5 border-2 border-indigo-400 border-t-transparent rounded-full animate-spin" />
        )}
        <span className={isThinking ? "text-neutral-300" : "text-neutral-500"}>
          {currentStatus}
        </span>
      </div>

      {/* History Toggle - Only show if there's history */}
      {historyLines.length > 0 && (
        <>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className="flex items-center gap-1 text-[10px] text-neutral-600 hover:text-neutral-400 transition-colors ml-1"
          >
            {showHistory ? (
              <ExpandLess sx={{ fontSize: 12 }} />
            ) : (
              <ExpandMore sx={{ fontSize: 12 }} />
            )}
            <span>
              {showHistory ? "Hide" : "Show"} {historyLines.length} previous
              step{historyLines.length > 1 ? "s" : ""}
            </span>
          </button>

          {showHistory && (
            <div className="mt-2 ml-3 pl-2 border-l border-neutral-800">
              {historyLines.map((line, idx) => (
                <div key={idx} className="text-[10px] text-neutral-600 py-0.5">
                  {line}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
};
