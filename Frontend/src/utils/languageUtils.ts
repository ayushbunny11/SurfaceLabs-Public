export const getLanguageFromFilename = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    
    switch (ext) {
        // JavaScript / TypeScript
        case 'js':
        case 'jsx':
        case 'mjs':
        case 'cjs':
            return 'javascript';
        case 'ts':
        case 'tsx':
            return 'typescript';
            
        // Python
        case 'py':
            return 'python';
            
        // Web
        case 'html':
        case 'htm':
            return 'html';
        case 'css':
        case 'scss':
        case 'sass':
        case 'less':
            return 'css';
        case 'json':
            return 'json';
            
        // Other
        case 'md':
        case 'markdown':
            return 'markdown';
        case 'yaml':
        case 'yml':
            return 'yaml';
        case 'sh':
        case 'bash':
            return 'bash';
        case 'go':
            return 'go';
        case 'rs':
        case 'rust':
            return 'rust';
        case 'java':
            return 'java';
        case 'c':
        case 'cpp':
        case 'h':
        case 'hpp':
            return 'cpp';
            
        default:
            return 'text';
    }
};
