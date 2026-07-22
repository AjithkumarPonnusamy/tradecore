"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type WorkspaceMode = "market" | "journal";

interface WorkspaceContextType {
  activeWorkspace: WorkspaceMode;
  setActiveWorkspace: (mode: WorkspaceMode) => void;
  toggleWorkspace: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export const WorkspaceProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [activeWorkspace, setActiveWorkspaceState] = useState<WorkspaceMode>("market");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem("active_workspace") as WorkspaceMode;
    if (saved === "market" || saved === "journal") {
      setActiveWorkspaceState(saved);
    }
  }, []);

  const setActiveWorkspace = (mode: WorkspaceMode) => {
    setActiveWorkspaceState(mode);
    if (typeof window !== "undefined") {
      localStorage.setItem("active_workspace", mode);
    }
  };

  const toggleWorkspace = () => {
    const next = activeWorkspace === "market" ? "journal" : "market";
    setActiveWorkspace(next);
  };

  return (
    <WorkspaceContext.Provider value={{ activeWorkspace, setActiveWorkspace, toggleWorkspace }}>
      {children}
    </WorkspaceContext.Provider>
  );
};

export const useWorkspace = () => {
  const context = useContext(WorkspaceContext);
  if (!context) {
    throw new Error("useWorkspace must be used within a WorkspaceProvider");
  }
  return context;
};
