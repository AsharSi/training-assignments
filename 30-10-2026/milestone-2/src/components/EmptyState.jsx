function EmptyState({ title, message, children }) {
  return (
    <div className="empty-state" role="status">
      <h3>{title}</h3>
      {message && <p>{message}</p>}
      {children}
    </div>
  )
}

export default EmptyState
