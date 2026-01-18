import { type FC, useContext, useEffect } from "react";
import { Code } from "@mui/icons-material";
import { AppContext } from "../../../context/AppContext";
import { ActiveFeatures } from "./ActiveFeatures";
import { ProjectFiles } from "./ProjectFiles";

export const Sidebar: FC = () => {
  const { repoData, checkSystemHealth, isSystemOnline } =
    useContext(AppContext);

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
        <ActiveFeatures />
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
          <span className="font-mono opacity-50">Tokens: 4k</span>
        </div>
      </div>
    </div>
  );
};
