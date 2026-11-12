import { NavLink } from 'react-router-dom'

function Navbar({ registrationCount }) {
  return (
    <header className="navbar">
      <div className="navbar-inner">
        <NavLink to="/" className="brand">
          Community Learning Centre
        </NavLink>
        <nav className="nav-links" aria-label="Main">
          <NavLink to="/" end>
            Events
          </NavLink>
          <NavLink to="/registrations">
            Registrations
            <span className="badge" aria-label={`${registrationCount} registrations`}>
              {registrationCount}
            </span>
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

export default Navbar
