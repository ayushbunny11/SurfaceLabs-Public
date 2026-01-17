import React, { createContext, useState } from 'react';
import { AppView } from '../types';
import type { AppContextType } from '../types';
import { MOCK_SESSIONS } from '../constants';
import type { RepoData, Message, Session } from '../types';

export const AppContext = createContext<AppContextType>({
    currentView: AppView.LANDING,
    repoData: null,
    messages: [],
    sessions: [],
    activeFile: null,
    setView: () => { },
    setRepoData: () => { },
    addMessage: () => { },
    resetApp: () => { },
    setActiveFile: () => { },
});


export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentView, setView] = useState<AppView>(AppView.WORKSPACE);
    const [repoData, setRepoData] = useState<RepoData | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessions] = useState<Session[]>(MOCK_SESSIONS);
    const [activeFile, setActiveFile] = useState<{ name: string; path: string; content: string | null } | null>(null);

    const addMessage = (msg: Message) => {
        setMessages(prev => [...prev, msg]);
    };

    const resetApp = () => {
        setView(AppView.LANDING);
        setRepoData(null);
        setMessages([]);
        setActiveFile(null);
    };

    const contextValue = {
        currentView,
        repoData,
        messages,
        sessions,
        activeFile,
        setView,
        setRepoData,
        addMessage,
        resetApp,
        setActiveFile
    };

    return (
        <AppContext.Provider value={contextValue}>
            {children}
        </AppContext.Provider>
    );
};
