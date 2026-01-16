import React, { useState } from 'react';
import { AppView } from './types';
import type { RepoData, Message, Session } from './types';
import { AppContext } from './context/AppContext';
import LandingView from './components/LandingView';
import { MOCK_SESSIONS } from './constants';

// Placeholder for now
const WorkspaceView = () => <div>Workspace View</div>;

const App: React.FC = () => {
  const [currentView, setView] = useState<AppView>(AppView.LANDING);
  const [repoData, setRepoData] = useState<RepoData | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const [sessions] = useState<Session[]>(MOCK_SESSIONS);

  const addMessage = (msg: Message) => {
    setMessages(prev => [...prev, msg]);
  };

  const resetApp = () => {
    setView(AppView.LANDING);
    setRepoData(null);
    setMessages([]);
  };

  const contextValue = {
    currentView,
    repoData,
    messages,
    sessions,
    setView,
    setRepoData,
    addMessage,
    resetApp
  };

  return (
    <AppContext.Provider value={contextValue}>
      <div className="antialiased text-neutral-200 bg-background min-h-screen selection:bg-primary/30 selection:text-white">
        {currentView === AppView.LANDING && <LandingView />}
        {currentView === AppView.ANALYSIS && <div>Analysis View Placeholder</div>}
        {currentView === AppView.WORKSPACE && <WorkspaceView />}
      </div>
    </AppContext.Provider>
  );
};

export default App;
