import { NavLink, Outlet } from "react-router-dom";
import { BarChart3, Car, Gauge, Search } from "lucide-react";

const nav = [
  { to: "/", label: "Accueil", icon: Car, end: true },
  { to: "/recherche", label: "Trouver une voiture", icon: Search },
  { to: "/analyse", label: "Analyser une annonce", icon: Gauge },
  { to: "/marche", label: "Signaux marché", icon: BarChart3 },
];

export function Layout() {
  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <NavLink to="/" className="logo">
            <span className="logo-icon">
              <Car size={22} />
            </span>
            <div>
              <strong>Auto Market</strong>
              <span>Marché occasion Maroc</span>
            </div>
          </NavLink>
          <nav className="header-nav">
            {nav.map(({ to, label, icon: Icon, end }) => (
              <NavLink key={to} to={to} end={end} className={({ isActive }) => (isActive ? "active" : "")}>
                <Icon size={17} />
                {label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
      <footer className="footer">
        <p>Données Avito Maroc · Estimation ML · Usage informatif uniquement</p>
      </footer>
    </div>
  );
}
