import { useState, type FC } from "react";
import { WorkspaceLayout } from "./Layout/WorkspaceLayout";
import { Sidebar } from "./Sidebar/Sidebar";
import { MainInterface } from "./Chat/MainInterface";

export const WorkspaceView: FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  return (
    <WorkspaceLayout
      sidebarOpen={sidebarOpen}
      onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
      sidebar={<Sidebar />}
      main={<MainInterface onToggleSidebar={() => setSidebarOpen(!sidebarOpen)} />}
    />
  );
};

export default WorkspaceView;