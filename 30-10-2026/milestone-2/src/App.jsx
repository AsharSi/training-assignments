import { Route, Routes } from 'react-router-dom'
import Navbar from './components/Navbar.jsx'
import { useRegistrations } from './hooks/useRegistrations.js'
import EventsPage from './pages/EventsPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import RegistrationsPage from './pages/RegistrationsPage.jsx'

function App() {
  const { registrations, bookedCounts, isEmailRegistered, addRegistration, cancelRegistration } =
    useRegistrations()

  return (
    <>
      <Navbar registrationCount={registrations.length} />
      <main className="container">
        <Routes>
          <Route
            path="/"
            element={
              <EventsPage
                bookedCounts={bookedCounts}
                isEmailRegistered={isEmailRegistered}
                onRegister={addRegistration}
              />
            }
          />
          <Route
            path="/registrations"
            element={
              <RegistrationsPage registrations={registrations} onCancel={cancelRegistration} />
            }
          />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
      <footer className="footer">Community Learning Centre · Event Enrollment Manager</footer>
    </>
  )
}

export default App
