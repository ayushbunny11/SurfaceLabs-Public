import type { RepoData, Session } from './types';

export const MOCK_REPO: RepoData = {
    url: 'https://github.com/facebook/react',
    name: 'react',
    owner: 'facebook',
    stars: 213000,
    branches: 142,
    language: 'TypeScript',
};

export const MOCK_SESSIONS: Session[] = [
    { id: '1', name: 'feat/stripe-payment-intent', date: 'In Progress' },
    { id: '2', name: 'fix/auth-token-refresh', date: 'Review Ready' },
    { id: '3', name: 'chore/upgrade-tailwind-v4', date: 'Merged' },
];

export const INITIAL_LOGS = [
    "Cloning repository...",
    "Analyzing directory structure...",
    "Mapping dependency graph...",
    "Identifying architectural patterns...",
    "Indexing component signatures...",
    "Loading style guidelines...",
    "Running static analysis checks...",
    "Environment ready for integration."
];

export const LANDING_FEATURES = [
    { label: 'Secure', color: 'bg-green-500' },
    { label: 'Private', color: 'bg-blue-500' },
    { label: 'Enterprise', color: 'bg-purple-500' },
    { label: 'Hackathon', color: 'bg-pink-500' },
];
