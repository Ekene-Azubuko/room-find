import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { Icon } from "./Icon";

/** Keep the Room Find wordmark and page navigation consistent. */
export function Header({ children }: { children?: ReactNode }) {
  return (
    <header className="site-header">
      <Link className="brand" to="/" aria-label="Room Find home">
        <span className="brand-icon">
          <Icon name="roomFind" />
        </span>
        Room Find
      </Link>
      <nav aria-label="Main navigation">{children}</nav>
    </header>
  );
}
