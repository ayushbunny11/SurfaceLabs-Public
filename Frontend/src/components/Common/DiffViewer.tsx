import React from 'react';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';

interface DiffViewerProps {
    oldCode: string;
    newCode: string;
    language?: string;
    splitView?: boolean;
}

const DiffViewer: React.FC<DiffViewerProps> = ({ 
    oldCode, 
    newCode, 
    // language = 'javascript', 
    splitView = false  // Unified view by default (single column)
}) => {
    
    const newStyles = {
        variables: {
            dark: {
                diffViewerBackground: '#171717', // neutral-900
                diffViewerColor: '#FFF',
                addedBackground: '#064e3b', // emerald-900
                addedColor: '#34d399', // emerald-400
                removedBackground: '#450a0a', // red-950
                removedColor: '#f87171', // red-400
                wordAddedBackground: '#065f46', // emerald-800
                wordRemovedBackground: '#7f1d1d', // red-900
                addedGutterBackground: '#064e3b',
                removedGutterBackground: '#450a0a',
                gutterBackground: '#171717',
                gutterColor: '#525252', // neutral-600
                codeFoldGutterBackground: '#262626', // neutral-800
                codeFoldBackground: '#262626',
                emptyLineBackground: '#171717',
                gutterBorder: '#262626',
                lineNumber: '#525252',
                lineNumberColor: '#737373', // neutral-500
            }
        },
        line: {
            padding: '4px 0',
            lineHeight: '1.5',
            fontSize: '13px',
            fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace',
        }
    };

    return (
        <div className="rounded-lg overflow-hidden border border-neutral-800">
            <ReactDiffViewer
                oldValue={oldCode}
                newValue={newCode}
                splitView={splitView}
                compareMethod={DiffMethod.WORDS}
                useDarkTheme={true}
                styles={newStyles}
                // We could map 'language' to prism languages here if needed, 
                // but default highlighting is often sufficient or handled by passed renderContent
            />
        </div>
    );
};

export default DiffViewer;
