import { type FC, useContext } from "react";
import { Add, AccountTree } from "@mui/icons-material";
import { AppContext } from "../../../context/AppContext";

export const ActiveFeatures: FC = () => {
  const { sessions } = useContext(AppContext);

  return (
    <div className="mb-6">
        <div className="px-4 mb-2 flex items-center justify-between group">
            <span className="text-xs font-semibold text-neutral-500 uppercase tracking-wider group-hover:text-neutral-400 transition-colors">
                Active Features
            </span>
            <button className="text-neutral-600 hover:text-neutral-300 transition-colors">
                <Add sx={{ fontSize: 16 }} />
            </button>
        </div>

        <nav className="space-y-0.5 px-2">
            {sessions.map((session, index) => (
                <button
                    key={session.id || index}
                    className="w-full text-left px-3 py-2.5 rounded-md text-sm text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800 transition-all group"
                >
                    <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-neutral-300">
                            <AccountTree sx={{ fontSize: 14 }} className="text-indigo-500" />
                            <span className="truncate font-medium">{session.name}</span>
                        </div>
                        <div className="flex justify-between items-center pl-6">
                            <span className="text-[10px] text-neutral-600 group-hover:text-neutral-500">
                                {session.date}
                            </span>
                        </div>
                    </div>
                </button>
            ))}
            {sessions.length === 0 && (
                <div className="px-3 py-4 text-xs text-neutral-600 text-center italic">
                    No active sessions
                </div>
            )}
        </nav>
    </div>
  );
};
