import React, { createContext, useState, useEffect } from 'react';
import { AppView } from '../types';
import type { AppContextType } from '../types';
import { MOCK_SESSIONS } from '../constants';
import type { RepoData, Message, Session } from '../types';
import { system_health } from '../configs/api_config';
import api from '../services/api';

export const AppContext = createContext<AppContextType>({
    currentView: AppView.LANDING,
    repoData: null,
    messages: [],
    sessions: [],
    isSystemOnline: null,
    activeFile: null,
    setView: () => { },
    setRepoData: () => { },
    addMessage: () => { },
    resetApp: () => { },
    checkSystemHealth: async () => { },
    setActiveFile: () => { },
});


export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [currentView, setView] = useState<AppView>(AppView.WORKSPACE);
    const [repoData, setRepoData] = useState<RepoData | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessions] = useState<Session[]>(MOCK_SESSIONS);
    const [activeFile, setActiveFile] = useState<{ name: string; path: string; content: string | null } | null>(null);
    const [isSystemOnline, setIsSystemOnline] = useState<boolean | null>(null);

    const checkSystemHealth = async () => {
        try {
            const status = await api.get(system_health);
            console.log(status);
            setIsSystemOnline(status.data.status === 'ok');
        } catch (error) {
            console.error('System health check failed:', error);
            setIsSystemOnline(false);
        }
    };

    // Check system health on mount
    useEffect(() => {
        checkSystemHealth();
    }, []);

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
        isSystemOnline,
        activeFile,
        setView,
        setRepoData,
        addMessage,
        resetApp,
        checkSystemHealth,
        setActiveFile
    };

    return (
        <AppContext.Provider value={contextValue}>
            {children}
        </AppContext.Provider>
    );
};
