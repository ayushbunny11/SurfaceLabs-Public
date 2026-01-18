import React, { useState, useContext } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AppContext } from "../context/AppContext";
import { AppView } from "../types";
import { LANDING_FEATURES } from "../constants";
import {
  GitHub,
  Search,
  ArrowRight,
  Code,
  AccountTree,
  Star,
  Build,
} from "@mui/icons-material";
import {
  Button,
  TextField,
  InputAdornment,
  Chip,
  Alert,
  Snackbar,
  LinearProgress,
  Box,
  Typography,
} from "@mui/material";
import { parse_github_url_stream } from "../configs/api_config";
import { streamSSE } from "../utils/sse";

// Helper to format relative time (e.g., "2 hours ago", "3 days ago")
const formatRelativeTime = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);
  const diffMinutes = Math.floor(diffSeconds / 60);
  const diffHours = Math.floor(diffMinutes / 60);
  const diffDays = Math.floor(diffHours / 24);
  const diffWeeks = Math.floor(diffDays / 7);
  const diffMonths = Math.floor(diffDays / 30);

  if (diffMonths > 0)
    return `${diffMonths} month${diffMonths > 1 ? "s" : ""} ago`;
  if (diffWeeks > 0) return `${diffWeeks} week${diffWeeks > 1 ? "s" : ""} ago`;
  if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;
  if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
  if (diffMinutes > 0)
    return `${diffMinutes} min${diffMinutes > 1 ? "s" : ""} ago`;
  return "just now";
};

const LandingView: React.FC = () => {
  const { setView, setRepoData, repoData, isSystemOnline } =
    useContext(AppContext);
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [repoFound, setRepoFound] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Progress state for SSE
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setLoading(true);
    setError(null);
    setProgress(0);
    setProgressMessage("Starting...");

    try {
      let metadataReceived: any = null;
      let cloneInfo: any = null;

      await streamSSE(
        parse_github_url_stream,
        { github_repo: url },
        {
          onProgress: (percent, message) => {
            setProgress(percent);
            setProgressMessage(message);
          },
          onMetadata: (data) => {
            metadataReceived = data;
          },
          onComplete: (data) => {
            cloneInfo = data;
            setProgress(100);
            setProgressMessage("Complete!");
          },
          onError: (msg) => {
            throw new Error(msg);
          },
        },
      );

      // Check if we got metadata - if not, something went wrong
      if (!metadataReceived) {
        throw new Error("Failed to receive repository data. Please try again.");
      }

      // Set repo data from collected metadata and clone info
      setRepoData({
        url: url,
        name: metadataReceived.repo,
        owner: metadataReceived.owner,
        stars: metadataReceived.stars ?? 0,
        branches: metadataReceived.branches ?? 0,
        language: metadataReceived.language ?? "Unknown",
        updatedAt: metadataReceived.updated_at,
        isPrivate: metadataReceived.is_private ?? false,
        description: metadataReceived.description,
        cloneId: cloneInfo?.unique_id,
        clonePath: cloneInfo?.path,
      });

      setRepoFound(true);
    } catch (err: any) {
      console.error("Failed to parse GitHub URL:", err);

      // User-friendly error messages
      let errorMessage =
        "Failed to load repository. Please check the URL and try again.";
      if (err.message) {
        if (
          err.message.includes("Failed to fetch") ||
          err.message.includes("NetworkError")
        ) {
          errorMessage =
            "Network error. Please check your connection and try again.";
        } else if (err.message.includes("connect")) {
          errorMessage =
            "Cannot connect to server. Please make sure the backend is running.";
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
      setRepoFound(false);
    } finally {
      setLoading(false);
      setProgress(0);
      setProgressMessage("");
    }
  };

  const handleProceed = () => {
    setView(AppView.WORKSPACE);
  };

  // Assuming 'view' is also available from AppContext, or passed as a prop
  // For this change, we'll assume it's available in the scope where LandingView is rendered
  // and that WorkspaceView is imported.
  // This part of the instruction seems to imply LandingView itself should conditionally render WorkspaceView.
  // However, without the full context of how LandingView is used, this might be a structural change.
  // Sticking to the exact instruction, if 'view' is a state managed higher up, this block would be there.
  // If 'view' is from AppContext, we'd need to destructure it: const { setView, setRepoData, repoData, view } = useContext(AppContext);
  // For now, I'll add it as if 'view' is accessible.
  // Note: WorkspaceView import is missing in the provided content, assuming it exists.
  // import WorkspaceView from "./WorkspaceView"; // This would be needed if this block is active.

  return (
    <div className="h-screen w-full flex flex-col items-center justify-center p-6 relative overflow-hidden bg-background">
      {/* Background ambient glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-900/10 blur-[120px] rounded-full pointer-events-none" />

      {/* System Status Indicator */}
      <div className="absolute top-4 right-4">
        <Chip
          icon={
            <span
              className={`w-2 h-2 rounded-full ${
                isSystemOnline
                  ? "bg-green-500"
                  : isSystemOnline === false
                    ? "bg-red-500"
                    : "bg-yellow-500"
              }`}
            />
          }
          label={
            isSystemOnline
              ? "System Online"
              : isSystemOnline === false
                ? "System Offline"
                : "Checking..."
          }
          variant="outlined"
          sx={{
            borderColor: isSystemOnline
              ? "rgba(34, 197, 94, 0.2)"
              : isSystemOnline === false
                ? "rgba(239, 68, 68, 0.2)"
                : "rgba(234, 179, 8, 0.2)",
            backgroundColor: isSystemOnline
              ? "rgba(34, 197, 94, 0.05)"
              : isSystemOnline === false
                ? "rgba(239, 68, 68, 0.05)"
                : "rgba(234, 179, 8, 0.05)",
            color: isSystemOnline
              ? "#4ade80"
              : isSystemOnline === false
                ? "#f87171"
                : "#facc15",
            "& .MuiChip-label": { px: 1.5 },
            "& .MuiChip-icon": { ml: 1 },
          }}
        />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg z-10"
      >
        <div className="text-center mb-10">
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-gradient-to-br from-neutral-800 to-black border border-neutral-800 mb-6 shadow-2xl"
          >
            <Build className="text-primary" sx={{ fontSize: 28 }} />
          </motion.div>
          <h1 className="text-4xl font-semibold tracking-tight text-white mb-3">
            Automated Feature Integration
          </h1>
          <p className="text-neutral-400 text-lg">
            Transform requirements into production-ready code.
          </p>
        </div>

        <AnimatePresence mode="wait">
          {!repoFound ? (
            <motion.form
              key="input-form"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              onSubmit={handleSearch}
              className="relative flex flex-col gap-6"
            >
              <TextField
                placeholder="https://github.com/organization/repository"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                autoFocus
                fullWidth
                variant="outlined"
                sx={{
                  "& .MuiOutlinedInput-root": {
                    backgroundColor: "var(--color-surface)", // neutral-900
                    color: "white",
                    borderRadius: "0.75rem", // rounded-xl
                    "& fieldset": {
                      borderColor: "var(--color-border)", // neutral-700
                    },
                    "&:hover fieldset": {
                      borderColor: "#a3a3a3", // neutral-400
                    },
                    "&.Mui-focused fieldset": {
                      borderColor: "var(--color-primary)", // primary-500
                    },
                  },
                }}
                slotProps={{
                  input: {
                    startAdornment: (
                      <InputAdornment position="start">
                        <GitHub sx={{ fontSize: 20, color: "#9ca3af" }} />
                      </InputAdornment>
                    ),
                  },
                }}
              />
              <div className="flex flex-col gap-3">
                {loading ? (
                  <Box sx={{ width: "100%" }}>
                    <LinearProgress
                      variant="determinate"
                      value={progress}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: "var(--color-surface)",
                        "& .MuiLinearProgress-bar": {
                          backgroundColor: "var(--color-primary)",
                          borderRadius: 4,
                        },
                      }}
                    />
                    <Typography
                      variant="caption"
                      sx={{
                        color: "#9ca3af",
                        mt: 1,
                        display: "block",
                        textAlign: "center",
                      }}
                    >
                      {progressMessage || "Loading..."}
                    </Typography>
                  </Box>
                ) : (
                  <Button
                    type="submit"
                    disabled={!url}
                    variant="contained"
                    fullWidth
                    sx={{
                      height: "3rem",
                      borderRadius: "0.5rem",
                      backgroundColor: "var(--color-primary)",
                      textTransform: "none",
                      fontSize: "1rem",
                      "&:hover": {
                        filter: "brightness(1.1)",
                        backgroundColor: "var(--color-primary)",
                      },
                      "&:disabled": {
                        opacity: 0.7,
                        backgroundColor: "var(--color-surface)",
                        color: "#6b7280",
                      },
                    }}
                    startIcon={<Search sx={{ fontSize: 18 }} />}
                  >
                    Load Repository
                  </Button>
                )}
              </div>
            </motion.form>
          ) : (
            <motion.div
              key="repo-card"
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ type: "spring", stiffness: 300, damping: 25 }}
            >
              <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-2xl relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 via-purple-500 to-indigo-500/50" />

                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-medium border ${
                          repoData?.isPrivate
                            ? "bg-yellow-500/10 text-yellow-500 border-yellow-500/20"
                            : "bg-green-500/10 text-green-500 border-green-500/20"
                        }`}
                      >
                        {repoData?.isPrivate ? "Private" : "Public"}
                      </span>
                      {repoData?.updatedAt && (
                        <span className="text-xs text-neutral-500">
                          Updated {formatRelativeTime(repoData.updatedAt)}
                        </span>
                      )}
                    </div>
                    <h2 className="text-xl font-medium text-white flex items-center gap-2">
                      {repoData?.owner} /{" "}
                      <span className="text-indigo-500">{repoData?.name}</span>
                    </h2>
                  </div>
                  <div className="p-2 bg-neutral-900 rounded-lg border border-neutral-800 text-neutral-400">
                    <GitHub sx={{ fontSize: 24 }} />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-black rounded-lg p-3 border border-neutral-800">
                    <div className="text-xs text-neutral-500 mb-1 flex items-center gap-1">
                      <Star sx={{ fontSize: 14 }} /> Stars
                    </div>
                    <div className="font-mono text-sm text-white">
                      {repoData?.stars?.toLocaleString() ?? 0}
                    </div>
                  </div>
                  <div className="bg-black rounded-lg p-3 border border-neutral-800">
                    <div className="text-xs text-neutral-500 mb-1 flex items-center gap-1">
                      <AccountTree sx={{ fontSize: 14 }} /> Branches
                    </div>
                    <div className="font-mono text-sm text-white">
                      {repoData?.branches ?? 0}
                    </div>
                  </div>
                  <div className="bg-black rounded-lg p-3 border border-neutral-800">
                    <div className="text-xs text-neutral-500 mb-1 flex items-center gap-1">
                      <Code sx={{ fontSize: 14 }} /> Stack
                    </div>
                    <div className="font-mono text-sm text-indigo-500">
                      {repoData?.language ?? "Unknown"}
                    </div>
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button
                    variant="outlined"
                    onClick={() => setRepoFound(false)}
                    fullWidth
                    sx={{
                      color: "white",
                      borderColor: "#404040",
                      textTransform: "none",
                      "&:hover": {
                        borderColor: "#a3a3a3",
                        backgroundColor: "rgba(255, 255, 255, 0.05)",
                      },
                    }}
                  >
                    Back
                  </Button>
                  <Button
                    onClick={() => handleProceed()}
                    variant="contained"
                    fullWidth
                    endIcon={<ArrowRight sx={{ fontSize: 18 }} />}
                    sx={{
                      backgroundColor: "#4f46e5",
                      textTransform: "none",
                      "&:hover": {
                        backgroundColor: "#4338ca",
                      },
                    }}
                  >
                    Initialize Context
                  </Button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="mt-12 flex justify-center gap-6 text-neutral-600 text-xs font-mono uppercase tracking-widest">
          {LANDING_FEATURES.map((feature) => (
            <span key={feature.label} className="flex items-center gap-1">
              <span
                className={`w-1.5 h-1.5 rounded-full ${feature.color}`}
              ></span>
              {feature.label}
            </span>
          ))}
        </div>
      </motion.div>

      <Snackbar
        open={!!error}
        autoHideDuration={3000}
        anchorOrigin={{ vertical: "top", horizontal: "right" }}
        onClose={() => setError(null)}
      >
        <Alert
          onClose={() => setError(null)}
          severity="error"
          sx={{ width: "100%" }}
        >
          {error}
        </Alert>
      </Snackbar>
    </div>
  );
};

export default LandingView;
