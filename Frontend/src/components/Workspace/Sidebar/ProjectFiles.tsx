import { type FC, useEffect, useState, useContext } from "react";
import {
  Folder,
  FolderOpen,
  InsertDriveFile,
  ExpandMore,
  ChevronRight,
} from "@mui/icons-material";
import api, { apiRequest } from "../../../services/api";
import { repo_tree, repo_content } from "../../../configs/api_config";
import { AppContext } from "../../../context/AppContext";

interface FileNode {
  name: string;
  path: string;
  type: "file" | "directory";
  children?: FileNode[] | null;
}

interface RepoTreeResponse {
  status: string;
  message: string;
  data: FileNode[];
}

interface FileContentResponse {
  status: string;
  message: string;
  data: string;
}

const FileTreeNode: FC<{ node: FileNode; depth?: number }> = ({
  node,
  depth = 0,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const { setActiveFile } = useContext(AppContext);
  const isFolder = node.type === "directory";
  const paddingLeft = `${depth * 12 + 12}px`;

  const handleClick = async () => {
    if (isFolder) {
      setIsOpen(!isOpen);
    } else {
      // Fetch Content
      try {
        // Optimistically set active file with loading state or partial data
        setActiveFile({
          name: node.name,
          path: node.path,
          content: "Loading...",
        });

        const res = await apiRequest<FileContentResponse>("POST", repo_content, {
          folder_id: "3000ffa4303f4d1fb92a60b107462df2",
          file_path: node.path,
        });

        if (res.status === "success") {
          setActiveFile({
            name: node.name,
            path: node.path,
            content: res.data,
          });
        }
      } catch (error) {
        console.error("Failed to fetch file content", error);
        setActiveFile({
          name: node.name,
          path: node.path,
          content: "Error loading content",
        });
      }
    }
  };

  return (
    <div>
      <div
        onClick={handleClick}
        className={`
            flex items-center gap-1.5 py-1 pr-2 hover:bg-[#2a2a2a] cursor-pointer select-none text-neutral-400 hover:text-neutral-200 transition-colors
            ${!isFolder ? "text-neutral-400" : "text-neutral-300"}
        `}
        style={{ paddingLeft }}
      >
        {isFolder && (
          <span className="opacity-70 flex items-center">
            {isOpen ? (
              <ExpandMore sx={{ fontSize: 14 }} />
            ) : (
              <ChevronRight sx={{ fontSize: 14 }} />
            )}
          </span>
        )}
        {!isFolder && <span className="w-[14px]"></span>}

        {isFolder ? (
          isOpen ? (
            <FolderOpen sx={{ fontSize: 14, color: "#fbbf24" }} />
          ) : (
            <Folder sx={{ fontSize: 14, color: "#fbbf24" }} />
          )
        ) : (
          <InsertDriveFile sx={{ fontSize: 14, opacity: 0.7 }} />
        )}

        <span className="text-[13px] truncate font-sans">{node.name}</span>
      </div>

      {isFolder && isOpen && node.children && (
        <div>
          {node.children.map((child) => (
            <FileTreeNode key={child.path} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

export const ProjectFiles: FC = () => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadTree = async () => {
      setLoading(true);
      try {
        // Direct API call
        const response = await api.post<RepoTreeResponse>(repo_tree, {
          folder_id: "3000ffa4303f4d1fb92a60b107462df2",
        });

        if (response.data.status === "success") {
          setFileTree(response.data.data);
        }
      } catch (error) {
        console.error("Failed to load file tree", error);
      } finally {
        setLoading(false);
      }
    };

    loadTree();
  }, []);

  return (
    <div>
      <div className="px-4 mb-2 text-xs font-semibold text-neutral-500 uppercase tracking-wider">
        Project Files
      </div>
      <div className="mt-1">
        {loading ? (
          <div className="px-4 text-xs text-neutral-500 animate-pulse">
            Loading files...
          </div>
        ) : (
          <div>
            {fileTree.map((node) => (
              <FileTreeNode key={node.path} node={node} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
