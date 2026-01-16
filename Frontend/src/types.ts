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
    timestamp: number;
    reasoning?: string; // For the "Thinking" accordion
    isThinking?: boolean;
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
    setView: (view: AppView) => void;
    setRepoData: (data: RepoData) => void;
    addMessage: (msg: Message) => void;
    resetApp: () => void;
}
