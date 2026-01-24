import React, { createContext, useState, useEffect, useCallback } from "react";
import { AppView } from "../types";
import type { AppContextType, CodeProposal } from "../types";
import { MOCK_SESSIONS } from "../constants";
import type { RepoData, Message, Session } from "../types";
import { system_health } from "../configs/api_config";
import api from "../services/api";

export const AppContext = createContext<AppContextType>({
  currentView: AppView.LANDING,
  repoData: null,
  messages: [],
  sessions: [],
  isSystemOnline: null,
  activeFile: null,
  setView: () => {},
  setRepoData: () => {},
  addMessage: () => {},
  resetApp: () => {},
  checkSystemHealth: async () => {},
  setActiveFile: () => {},
  sessionUsage: {
    prompt_tokens: 0,
    candidates_tokens: 0,
    cached_tokens: 0,
    total_tokens: 0,
  },
  setSessionUsage: () => {},
  // Multi-file proposal support
  pendingProposals: new Map(),
  addProposal: () => {},
  removeProposal: () => {},
  getProposal: () => undefined,
});

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [currentView, setView] = useState<AppView>(AppView.LANDING);
  const [repoData, setRepoData] = useState<RepoData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessions] = useState<Session[]>(MOCK_SESSIONS);
  const [activeFile, setActiveFile] = useState<{
    name: string;
    path: string;
    content: string | null;
    pendingContent?: string | null;
  } | null>(null);
  const [isSystemOnline, setIsSystemOnline] = useState<boolean | null>(null);
  const [sessionUsage, setSessionUsage] = useState({
    prompt_tokens: 0,
    candidates_tokens: 0,
    cached_tokens: 0,
    total_tokens: 0,
  });
  
  // Multi-file proposal support - store proposals by file path
  const [pendingProposals, setPendingProposals] = useState<Map<string, CodeProposal>>(new Map());

  // Add a proposal to the map (or update existing one for same file)
  const addProposal = useCallback((proposal: CodeProposal) => {
    console.log(`[AppContext] Adding proposal for: ${proposal.filePath}`);
    setPendingProposals(prev => {
      const newMap = new Map(prev);
      newMap.set(proposal.filePath, proposal);
      console.log(`[AppContext] Pending proposals count: ${newMap.size}`);
      return newMap;
    });
  }, []);

  // Remove a proposal from the map
  const removeProposal = useCallback((filePath: string) => {
    console.log(`[AppContext] Removing proposal for: ${filePath}`);
    setPendingProposals(prev => {
      const newMap = new Map(prev);
      newMap.delete(filePath);
      return newMap;
    });
  }, []);

  // Get a proposal by file path
  const getProposal = useCallback((filePath: string): CodeProposal | undefined => {
    return pendingProposals.get(filePath);
  }, [pendingProposals]);

  const checkSystemHealth = async () => {
    try {
      const status = await api.get(system_health);
      console.log(status);
      setIsSystemOnline(status.data.status === "ok");
    } catch (error) {
      console.error("System health check failed:", error);
      setIsSystemOnline(false);
    }
  };

  // Check system health on mount
  useEffect(() => {
    checkSystemHealth();
  }, []);

  // Listen for CODE_PROPOSAL events from chat stream
  useEffect(() => {
    const handleCodeProposal = (event: CustomEvent) => {
      const { filePath, originalContent, proposedContent, proposalId } = event.detail;
      console.log(`[AppContext] Received CODE_PROPOSAL for: ${filePath}`);

      // Add to pendingProposals map (doesn't overwrite other files!)
      addProposal({
        proposalId: proposalId || `proposal_${Date.now()}`,
        filePath,
        originalContent: originalContent || "",
        pendingContent: proposedContent,
        timestamp: Date.now()
      });

      // Also update activeFile if it matches this file (for immediate display)
      setActiveFile((prev) => {
        if (prev && (prev.path === filePath || prev.path.endsWith(filePath))) {
          // File is already open - update pendingContent
          return { ...prev, pendingContent: proposedContent, proposalId };
        }
        // If no file or different file is open, switch to this file
        const fileName =
          filePath.split("/").pop() || filePath.split("\\").pop() || filePath;
        return {
          name: fileName,
          path: filePath,
          content: originalContent || "",
          pendingContent: proposedContent,
          proposalId
        };
      });
    };

    window.addEventListener(
      "CODE_PROPOSAL",
      handleCodeProposal as EventListener,
    );
    return () =>
      window.removeEventListener(
        "CODE_PROPOSAL",
        handleCodeProposal as EventListener,
      );
  }, [addProposal]);

  const addMessage = (msg: Message) => {
    setMessages((prev) => [...prev, msg]);
  };

  const resetApp = () => {
    setView(AppView.LANDING);
    setRepoData(null);
    setMessages([]);
    setActiveFile(null);
    setSessionUsage({
      prompt_tokens: 0,
      candidates_tokens: 0,
      cached_tokens: 0,
      total_tokens: 0,
    });
    // Clear all pending proposals on reset
    setPendingProposals(new Map());
  };

  const contextValue = {
    currentView,
    repoData,
    messages,
    sessions,
    isSystemOnline,
    activeFile,
    setView,
    setRepoData,
    addMessage,
    resetApp,
    checkSystemHealth,
    setActiveFile,
    sessionUsage,
    setSessionUsage,
    // Multi-file proposal support
    pendingProposals,
    addProposal,
    removeProposal,
    getProposal,
  };

  return (
    <AppContext.Provider value={contextValue}>{children}</AppContext.Provider>
  );
};
