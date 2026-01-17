import { type FC, type ReactNode } from "react";
import { motion } from "framer-motion";

interface WorkspaceLayoutProps {
  sidebar: ReactNode;
  main: ReactNode;
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
}

export const WorkspaceLayout: FC<WorkspaceLayoutProps> = ({
  sidebar,
  main,
  sidebarOpen,
  onToggleSidebar,
}) => {
  return (
    <div className="flex h-screen w-full bg-[#0c0c0c] text-neutral-200 overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 md:hidden"
          onClick={onToggleSidebar}
        />
      )}

      {/* Sidebar Container */}
      <motion.aside
        initial={false}
        animate={{
          width: sidebarOpen ? 280 : 0,
          opacity: sidebarOpen ? 1 : 0,
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className={`fixed md:relative flex-shrink-0 h-full bg-[#121212] border-r border-neutral-800 z-50 overflow-hidden ${!sidebarOpen ? 'pointer-events-none md:pointer-events-auto' : ''}`}
        style={{ width: sidebarOpen ? 280 : 0 }}
      >
        <div className="w-[280px] h-full flex flex-col">
            {sidebar}
        </div>
      </motion.aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col h-full relative min-w-0 overflow-hidden">
        {main}
      </main>
    </div>
  );
};
