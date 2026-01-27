import { useRef, useEffect, useState, type FC } from "react";
import Typewriter from "typewriter-effect";
import { motion, AnimatePresence } from "framer-motion";
import {
  Close,
  CheckCircleOutline,
  KeyboardArrowRight,
  Wifi,
} from "@mui/icons-material";
import { Button } from "@mui/material";
import type { RepoData } from "../../types";

interface TerminalWindowProps {
  logs: {
    id?: string;
    message: string;
    timestamp: string;
    type: "info" | "success" | "process" | "error" | "warning";
  }[];
  completed: boolean;
  repoData: RepoData | null;
  onProceed: () => void;
  onAbort: () => void;
  status: "processing" | "success" | "failure";
}

const TypewriterText: FC<{ text: string }> = ({ text }) => {
  const [isTyping, setIsTyping] = useState(true);

  if (!isTyping) {
    return <span>{text}</span>;
  }

  return (
    <div className="inline-block">
      <Typewriter
        onInit={(typewriter) => {
          typewriter
            .typeString(text)
            .callFunction(() => setIsTyping(false))
            .start();
        }}
        options={{
          delay: 40,
          cursor: "█", 
        }}
      />
    </div>
  );
};

export const TerminalWindow: FC<TerminalWindowProps> = ({
  logs,
  completed,
  repoData,
  onProceed,
  onAbort,
  status
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="h-screen w-full bg-background flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Dynamic Background Elements */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-900/20 via-background to-background pointer-events-none" />
      <div className="absolute top-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-50" />
      <div className="absolute bottom-0 left-0 w-full h-[2px] bg-gradient-to-r from-transparent via-primary/30 to-transparent opacity-50" />

      {/* Grid Pattern Overlay */}
      <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>

      {/* Top Bar Navigation */}
      <motion.div
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="absolute top-6 left-6 right-6 flex justify-end items-end z-20"
      >
        <Button
          variant="text"
          onClick={onAbort}
          startIcon={<Close sx={{ fontSize: 18 }} />}
          sx={{
            color: "#737373",
            textTransform: "none",
            fontSize: "0.875rem",
            borderRadius: "9999px",
            px: 2,
            "&:hover": {
              color: "#ef4444",
              backgroundColor: "rgba(239, 68, 68, 0.1)",
            },
          }}
        >
          Abort Process
        </Button>
      </motion.div>

      {/* Main Terminal Window */}
      <motion.div
        layoutId="terminal-window"
        className="w-full max-w-3xl bg-[#0c0c0c]/90 backdrop-blur-xl border border-neutral-800/80 rounded-xl overflow-hidden shadow-2xl flex flex-col h-[600px] z-10 relative group"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        {/* Glow effect on hover */}
        <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-xl blur opacity-30 group-hover:opacity-50 transition duration-1000"></div>

        {/* Terminal Header */}
        <div className="h-11 bg-[#121212] border-b border-neutral-800 flex items-center px-4 justify-between shrink-0 relative z-10">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5 mr-4">
              <div className="w-3 h-3 rounded-full bg-[#ef4444]" />
              <div className="w-3 h-3 rounded-full bg-[#eab308]" />
              <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
            </div>
            <div className="flex items-center gap-2 px-3 py-1 bg-neutral-900/50 rounded text-xs font-mono text-neutral-400 border border-neutral-800">
              <Wifi
                sx={{ fontSize: 12 }}
                className={
                  status === "processing"
                    ? "text-green-500 animate-pulse"
                    : status === "failure"
                    ? "text-red-500"
                    : "text-neutral-600"
                }
              />
              <span>{status === "success" ? "Disconnected" : status === "failure" ? "Connection Failed" : "Live Connection"}</span>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-neutral-500">
            <span>SurfaceLabs-cli</span>
            <span className="text-neutral-700">—</span>
            <span>v2.4.0</span>
          </div>
        </div>

        {/* Terminal Body */}
        <div
          ref={scrollRef}
          className="flex-1 p-6 overflow-y-auto font-mono text-sm scrollbar-thin scrollbar-thumb-neutral-700 scrollbar-track-transparent relative z-10 bg-[#09090b]/50"
        >
          <div className="flex flex-col gap-1.5">
            <div className="text-neutral-500 mb-4 text-xs select-none">
              Last login: {new Date().toDateString()} on ttys001
            </div>
            
            {logs.map((log, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-start gap-3 group/line"
              >
                <span className="text-neutral-700 text-xs mt-0.5 w-14 font-mono select-none text-right">
                  {log.timestamp}
                </span>
                <div className="flex-1 flex items-start gap-2">
                  <span
                    className={`text-xs mt-0.5 select-none ${
                        log.type === "success" ? "text-green-500" : 
                        log.type === "info" ? "text-blue-500" : 
                        log.type === "error" ? "text-red-500" :
                        log.type === "warning" ? "text-yellow-500" :
                        "text-neutral-600"
                    }`}
                  >
                    ➜
                  </span>
                  <span
                    className={`
                        ${log.type === "success" ? "text-green-400 font-medium" : ""}
                        ${log.type === "info" ? "text-blue-300" : ""}
                        ${log.type === "process" ? "text-neutral-300" : ""}
                        ${log.type === "error" ? "text-red-400 font-medium" : ""}
                        ${log.type === "warning" ? "text-yellow-400" : ""}
                    `}
                  >
                   <TypewriterText key={log.message} text={log.message} />
                  </span>
                </div>
                {log.type === "success" && (
                  <CheckCircleOutline
                    sx={{ fontSize: 14 }}
                    className="text-green-500/50 mt-0.5 opacity-0 group-hover/line:opacity-100 transition-opacity"
                  />
                )}
              </motion.div>
            ))}

            {status === "processing" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex items-center gap-3 mt-2"
              >
                <span className="text-neutral-700 text-xs w-14 text-right">
                  ...
                </span>
                <div className="flex items-center gap-2">
                  <div className="w-2 h-4 bg-primary animate-pulse" />
                </div>
              </motion.div>
            )}
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-neutral-800 bg-[#121212] relative z-10 min-h-[72px] flex items-center justify-between">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  status === "success" ? "bg-green-500" : 
                  status === "failure" ? "bg-red-500" :
                  "bg-yellow-500 animate-pulse"
                }`}
              ></div>
              <span className={`text-xs font-medium ${status === "failure" ? "text-red-400" : "text-neutral-300"}`}>
                {status === "success" ? "Analysis Successful" : status === "failure" ? "Analysis Failed" : "Processing Repository..."}
              </span>
            </div>
            <span className="text-[10px] text-neutral-600 ml-4 mt-0.5">
              {status === "success"
                ? "Session ready for initialization"
                : status === "failure" 
                ? "Please check repo permissions or URL"
                : "Do not close this window"}
            </span>
          </div>

          <AnimatePresence>
            {(status === "success" || status === "failure") && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
              >
                <Button
                  variant="contained"
                  onClick={onProceed}
                  disabled={status === "failure"}
                  endIcon={<KeyboardArrowRight />}
                  sx={{
                    backgroundColor: "#16a34a", // Green-600
                    fontWeight: 500,
                    px: 3,
                    py: 1,
                    textTransform: "none",
                    borderRadius: "0.5rem",
                    boxShadow: status === "success" ? "0 0 20px rgba(34, 197, 94, 0.3)" : "none",
                    "&:hover": {
                      backgroundColor: "#15803d", // Green-700
                      boxShadow: status === "success" ? "0 0 30px rgba(34, 197, 94, 0.5)" : "none",
                    },
                    "&.Mui-disabled": {
                      backgroundColor: "#ef4444", // Red-500
                      color: "rgba(255, 255, 255, 0.7)",
                      boxShadow: "none"
                    }
                  }}
                >
                  {status === "failure" ? "Analysis Failed" : "Enter Workspace"}
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.div>
    </div>
  );
};
