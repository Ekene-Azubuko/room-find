import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { Icon } from "./Icon";

/** Keep the Roomly wordmark and page navigation consistent. */
export function Header({ children }: { children?: ReactNode }) {
  return (
    <header className="site-header">
      <Link className="brand" to="/" aria-label="Roomly home">
        <span className="brand-icon">
          <Icon name="home" />
        </span>
        Roomly
      </Link>
      <nav aria-label="Main navigation">{children}</nav>
    </header>
  );
}
