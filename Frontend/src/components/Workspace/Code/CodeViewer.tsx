import { type FC, useContext, useState } from "react";
import { Code, Preview, Visibility } from "@mui/icons-material";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import ts from "react-syntax-highlighter/dist/esm/languages/prism/typescript";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import markdown from "react-syntax-highlighter/dist/esm/languages/prism/markdown";
import json from "react-syntax-highlighter/dist/esm/languages/prism/json";
import css from "react-syntax-highlighter/dist/esm/languages/prism/css";
import html from "react-syntax-highlighter/dist/esm/languages/prism/markup";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { AppContext } from "../../../context/AppContext";
import { getLanguageFromFilename } from "../../../utils/languageUtils";
import "./CodeViewer.css";

// Register languages to ensure they are available
SyntaxHighlighter.registerLanguage("typescript", ts);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("markdown", markdown);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("css", css);
SyntaxHighlighter.registerLanguage("html", html);
SyntaxHighlighter.registerLanguage("bash", bash);

export const CodeViewer: FC = () => {
  const { activeFile } = useContext(AppContext);
  const [viewMode, setViewMode] = useState<"code" | "preview">("preview");

  if (!activeFile) {
    return (
      <div className="flex-1 bg-[#0c0c0c] flex items-center justify-center text-neutral-600 border-r border-neutral-800">
        <div className="text-center">
          <div className="text-4xl mb-4 opacity-20">⌘</div>
          <p className="text-sm">Select a file to view</p>
          <div className="mt-4 flex items-center justify-center gap-2 text-xs opacity-50">
            <Code sx={{ fontSize: 14 }} />
            <span>No file active</span>
          </div>
        </div>
      </div>
    );
  }

  const language = getLanguageFromFilename(activeFile.name);
  const isMarkdown = language === "markdown";

  return (
    <div className="flex-1 bg-[#0c0c0c] flex flex-col border-r border-neutral-800 overflow-hidden">
      {/* Header */}
      <div className="h-10 border-b border-neutral-800 flex items-center px-4 bg-[#0c0c0c] justify-between">
        <span className="text-xs font-mono text-neutral-400">
          {activeFile.path}
        </span>
        <div className="flex items-center gap-3">
          {isMarkdown && (
            <div className="flex bg-[#1e1e1e] rounded-md p-0.5 border border-neutral-800">
              <button
                onClick={() => setViewMode("code")}
                className={`px-2 py-0.5 text-[10px] rounded hover:text-white cursor-pointer transition-colors flex items-center gap-1 ${
                  viewMode === "code"
                    ? "bg-[#2a2a2a] text-white"
                    : "text-neutral-500"
                }`}
              >
                <Code sx={{ fontSize: 12 }} /> Code
              </button>
              <button
                onClick={() => setViewMode("preview")}
                className={`px-2 py-0.5 text-[10px] rounded hover:text-white cursor-pointer transition-colors flex items-center gap-1 ${
                  viewMode === "preview"
                    ? "bg-[#2a2a2a] text-white"
                    : "text-neutral-500"
                }`}
              >
                <Visibility sx={{ fontSize: 12 }} /> Preview
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-hidden flex flex-col bg-[#1e1e1e]">
        {/* If Markdown Preview Mode */}
        {isMarkdown && viewMode === "preview" ? (
          <div className="flex-1 overflow-auto p-8 markdown-body text-neutral-300 text-sm leading-relaxed bg-[#0d1117]">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code(props) {
                  const { children, className, node, ref, ...rest } = props;
                  const match = /language-(\w+)/.exec(className || "");
                  return match ? (
                    <SyntaxHighlighter
                      {...rest}
                      PreTag="div"
                      children={String(children).replace(/\n$/, "")}
                      language={match[1]}
                      style={vscDarkPlus}
                      customStyle={{
                        margin: 0,
                        padding: "1rem",
                        background: "#161b22",
                        fontSize: "13px",
                        borderRadius: "6px",
                        fontFamily: "monospace",
                      }}
                    />
                  ) : (
                    <code {...rest} className={className}>
                      {children}
                    </code>
                  );
                },
              }}
            >
              {activeFile.content || ""}
            </ReactMarkdown>
          </div>
        ) : (
          /* Code View Mode */
          <div className="flex-1 overflow-auto text-[13px] force-wrap">
            <SyntaxHighlighter
              language={language}
              style={vscDarkPlus}
              customStyle={{
                margin: 0,
                padding: "1.5rem 0", // Vertical padding only
                background: "transparent",
                fontSize: "13px",
                fontFamily: "'JetBrains Mono', 'Fira Code', monospace", // Better font stack
                lineHeight: "1.5",
              }}
              wrapLines={true}
              showLineNumbers={true}
              lineNumberStyle={{
                minWidth: "3.5em",
                paddingRight: "1em",
                color: "#6e7681",
                textAlign: "right",
                position: "absolute",
                left: 0,
                top: 0,
                background: "#1e1e1e", // Match editor bg
                borderRight: "1px solid #2b2b2b", // Subtle gutter styling
                height: "100%", // Not strictly necessary on row-by-row, but good for intent
              }}
              lineProps={{
                style: {
                  display: "block",
                  position: "relative",
                  paddingLeft: "4.5em", // Match gutter width + padding
                },
              }}
            >
              {activeFile.content || ""}
            </SyntaxHighlighter>
          </div>
        )}
      </div>

      {/* Footer (Status Bar) */}
      <div className="h-6 border-t border-neutral-800 bg-[#141414] flex items-center justify-between px-3 text-[10px] text-neutral-500 select-none shrink-0">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-1 hover:text-neutral-300 cursor-pointer transition-colors">
            <span>
              Total Lines{" "}
              {activeFile.content ? activeFile.content.split("\n").length : 0}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hover:text-neutral-300 cursor-pointer transition-colors">
            UTF-8
          </div>
          <div className="hover:text-neutral-300 cursor-pointer transition-colors uppercase font-medium">
            {language}
          </div>
          <div className="hover:text-neutral-300 cursor-pointer transition-colors">
            <span className="mr-1">🔔</span>
          </div>
        </div>
      </div>
    </div>
  );
};
