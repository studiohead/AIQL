import React from "react";
import { Link } from "react-router-dom";

const Topbar: React.FC = () => {
  return (
    <header className="topbar">
      <Link to="/Dashboard" className="logo">
        PIQL
      </Link>

      <div className="rightSection">
        <span className="profileBtn" tabIndex={0} role="button" aria-label="Profile">
          Profile
        </span>
        <span className="logoutBtn" tabIndex={0} role="button" aria-label="Logout">
          Logout
        </span>
      </div>
    </header>
  );
};

export default Topbar;
