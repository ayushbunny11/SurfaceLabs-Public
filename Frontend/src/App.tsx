import React from 'react';
import { AppView } from './types';
import { AppContext, AppProvider } from './context/AppContext';
import LandingView from './components/LandingView';
import AnalysisView from './components/AnalysisView';
import WorkspaceView from './components/Workspace/WorkspaceView';

const AppContent = () => {
    const { currentView } = React.useContext(AppContext);

    return (
        <div className="antialiased text-neutral-200 bg-background min-h-screen selection:bg-primary/30 selection:text-white">
            {currentView === AppView.LANDING && <LandingView />}
            {currentView === AppView.ANALYSIS && <AnalysisView />}
            {currentView === AppView.WORKSPACE && <WorkspaceView />}
        </div>
    );
};

const App = () => {
    return (
        <AppProvider>
            <AppContent />
        </AppProvider>
    );
};

export default App;
