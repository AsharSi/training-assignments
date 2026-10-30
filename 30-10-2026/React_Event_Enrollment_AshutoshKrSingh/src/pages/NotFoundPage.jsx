import { Link } from 'react-router-dom'
import EmptyState from '../components/EmptyState.jsx'

function NotFoundPage() {
  return (
    <EmptyState title="Page not found" message="The page you're looking for doesn't exist.">
      <Link to="/" className="btn btn-primary">
        Back to events
      </Link>
    </EmptyState>
  )
}

export default NotFoundPage
