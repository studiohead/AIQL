// frontend/src/layout/Topbar.tsx
import React from "react";
import { Link } from "react-router-dom";

const Topbar: React.FC = () => {
  return (
    <header
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "0.75rem 1rem",
        backgroundColor: "#1a73e8",
        color: "white",
        boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
        zIndex: 1000,
      }}
    >
      <Link
        to="/Dashboard"
        style={{
          color: "white",
          fontWeight: "bold",
          fontSize: "1.25rem",
          textDecoration: "none",
        }}
      >
        AIQL
      </Link>

      <div style={{ display: "flex", gap: "1rem" }}>
        <span style={{ cursor: "pointer" }}>Profile</span>
        <span style={{ cursor: "pointer" }}>Logout</span>
      </div>
    </header>
  );
};

export default Topbar;
