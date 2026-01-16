import { createContext } from 'react';
import { AppView } from '../types';
import type { AppContextType } from '../types';

export const AppContext = createContext<AppContextType>({
    currentView: AppView.LANDING,
    repoData: null,
    messages: [],
    sessions: [],
    setView: () => { },
    setRepoData: () => { },
    addMessage: () => { },
    resetApp: () => { },
});
