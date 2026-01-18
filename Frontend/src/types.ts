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
}

export interface Session {
    id: string;
    name: string;
    date: string;
}

export interface AppContextType {
    currentView: AppView;
    repoData: RepoData | null;
    messages: Message[];
    sessions: Session[];
    isSystemOnline: boolean | null;
    setView: (view: AppView) => void;
    setRepoData: (data: RepoData) => void;
    addMessage: (msg: Message) => void;
    resetApp: () => void;
    checkSystemHealth: () => Promise<void>;
    activeFile: { name: string; path: string; content: string | null } | null;
    setActiveFile: (file: { name: string; path: string; content: string | null } | null) => void;
}
