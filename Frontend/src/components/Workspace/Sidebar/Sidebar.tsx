import { type FC, useContext, useEffect } from "react";
import { Tooltip } from "@mui/material";
import { Code } from "@mui/icons-material";
import { AppContext } from "../../../context/AppContext";
import { ActiveFeatures } from "./ActiveFeatures";
import { ProjectFiles } from "./ProjectFiles";

const formatTokens = (num: number): string => {
  if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
  if (num >= 1000) return (num / 1000).toFixed(1) + 'k';
  return num.toString();
};

export const Sidebar: FC = () => {
  const { repoData, checkSystemHealth, isSystemOnline, sessionUsage } =
    useContext(AppContext);

  const { prompt_tokens, candidates_tokens, cached_tokens, total_tokens } = sessionUsage;
  const processed_tokens = prompt_tokens - cached_tokens;
  const saved_percent = Math.round((cached_tokens / prompt_tokens) * 100) || 0;

  useEffect(() => {
    checkSystemHealth();
  }, []);

  return (
    <div className="flex flex-col h-full bg-[#121212] border-r border-neutral-800 shrink-0">
      {/* Sidebar Header */}
      <div className="h-14 flex items-center px-4 border-b border-neutral-800 shrink-0 gap-3">
        <div className="w-8 h-8 rounded-lg bg-neutral-800 flex items-center justify-center text-neutral-300 border border-neutral-700">
          <Code fontSize="small" />
        </div>
        <div className="overflow-hidden">
          <h1 className="font-semibold text-sm text-neutral-200 truncate">
            {repoData?.name || "Repository"}
          </h1>
          <p className="text-xs text-neutral-500 truncate">
            {repoData?.owner || "Organization"}
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto py-4 scrollbar-thin scrollbar-thumb-neutral-800">
        {/* <ActiveFeatures /> */}
        <ProjectFiles />
      </div>

      {/* Footer Status */}
      <div className="p-4 border-t border-neutral-800 bg-[#121212]">
        <div className="flex items-center justify-between text-xs text-neutral-500">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-900 opacity-75"></span>
              <span
                className={`${isSystemOnline ? "bg-green-600" : "bg-red-600"} relative inline-flex rounded-full h-2 w-2`}
              ></span>
            </span>
            <span className="font-mono">
              {isSystemOnline ? "Online" : "Offline"}
            </span>
          </div>
           <Tooltip
            title={
                <div className="text-[10px] space-y-1.5 font-sans p-1">
                    <div className="flex justify-between gap-4 text-green-400">
                        <span>Cached Tokens:</span>
                        <span>{formatTokens(cached_tokens)}</span>
                    </div>
                    <div className="border-t border-white/10 my-1" />
                    <div className="flex justify-between gap-4 text-neutral-400">
                        <span>Processed Tokens:</span>
                        <span>{formatTokens(processed_tokens)}</span>
                    </div>
                    <div className="flex justify-between gap-4">
                        <span>Output:</span>
                        <span className="text-neutral-200">{formatTokens(candidates_tokens)}</span>
                    </div>
                    <div className="border-t border-white/10 my-1" />
                    <div className="flex justify-between gap-4 font-medium text-indigo-300">
                        <span>Billed Tokens:</span>
                        <span>{formatTokens(processed_tokens + candidates_tokens)}</span>
                    </div>
                </div>
            }
            arrow
            componentsProps={{
                tooltip: {
                    sx: {
                        bgcolor: '#1a1a1a',
                        border: '1px solid #262626',
                        color: '#a3a3a3',
                        p: 1.5,
                        borderRadius: 2,
                        boxShadow: 4
                    }
                },
                arrow: {
                    sx: {
                        color: '#1a1a1a'
                    }
                }
            }}
          >
            <div className="flex items-center gap-1.5 cursor-help transition-colors hover:text-neutral-300 opacity-70 hover:opacity-100">
                <span className="text-amber-500/80">⚡</span>
                <span className="font-mono text-[10px]">{formatTokens(total_tokens)}</span>
                 {cached_tokens > 0 && (
                    <span className="text-green-500/80 text-[9px] bg-green-500/10 px-1 rounded">
                        {saved_percent}%
                    </span>
                 )}
            </div>
          </Tooltip>
        </div>
      </div>
    </div>
  );
};
