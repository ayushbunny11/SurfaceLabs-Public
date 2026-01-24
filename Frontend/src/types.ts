export const AppView = {
    LANDING: 'LANDING',
    ANALYSIS: 'ANALYSIS',
    WORKSPACE: 'WORKSPACE'
} as const;

export type AppView = typeof AppView[keyof typeof AppView];

export interface RepoData {
    url: string;
    name: string;
    owner: string;
    stars: number;
    branches: number;
    language: string;
    // Metadata from GitHub API
    updatedAt?: string;
    isPrivate?: boolean;
    description?: string;
    // Clone info from backend
    cloneId?: string;
    clonePath?: string;
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
    reasoning?: string;
    isThinking?: boolean;
    stateChanges?: string[];
    citations?: { title: string; uri: string; type: string }[];
    usage?: {
        prompt_tokens: number;
        candidates_tokens: number;
        thoughts_tokens: number;
        cached_tokens: number;
        total_tokens: number;
    };
}

export interface Session {
    id: string;
    name: string;
    date: string;
}

// Code proposal from AI for diff viewer
export interface CodeProposal {
    proposalId: string;
    filePath: string;
    originalContent: string;
    pendingContent: string;
    timestamp: number;
}

export interface AppContextType {
    currentView: AppView;
    repoData: RepoData | null;
    messages: Message[];
    sessions: Session[];
    sessionUsage: {
        prompt_tokens: number;
        candidates_tokens: number;
        cached_tokens: number;
        total_tokens: number;
    };
    isSystemOnline: boolean | null;
    setView: (view: AppView) => void;
    setRepoData: (data: RepoData) => void;
    addMessage: (msg: Message) => void;
    resetApp: () => void;
    checkSystemHealth: () => Promise<void>;
    activeFile: { name: string; path: string; content: string | null; pendingContent?: string | null; proposalId?: string } | null;
    setActiveFile: (file: { name: string; path: string; content: string | null; pendingContent?: string | null; proposalId?: string } | null) => void;
    setSessionUsage: (usage: { prompt_tokens: number; candidates_tokens: number; cached_tokens: number; total_tokens: number; }) => void;
    // Multi-file proposal support
    pendingProposals: Map<string, CodeProposal>;
    addProposal: (proposal: CodeProposal) => void;
    removeProposal: (filePath: string) => void;
    getProposal: (filePath: string) => CodeProposal | undefined;
}
