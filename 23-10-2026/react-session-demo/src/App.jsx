import { useState } from "react"

function App() {
  const [username, setUsername] = useState("")
  const [loggedInUser, setLoggedInUser] = useState(
    sessionStorage.getItem("user") || ""
  )
  const [cartCount, setCartCount] = useState(0)

  function login() {
    setLoggedInUser(username)
    sessionStorage.setItem("user", username)
    setUsername("")
  }

  function logout() {
    setLoggedInUser("")
    setCartCount(0)

    sessionStorage.removeItem("user")
  }

  return (
    <div>
      <h1>React Session State Demo</h1>

      {!loggedInUser ? (
        <div>
          <h2>Login</h2>

          <input
            type="text"
            placeholder="Enter your name"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />

          <button onClick={login}>
            Login
          </button>
        </div>
      ) : (
        <div>
          <h2>Welcome {loggedInUser}</h2>

          <p>Cart Items: {cartCount}</p>

          <button onClick={() => setCartCount(cartCount + 1)}>
            Add Item
          </button>

          <button
            onClick={() =>
              setCartCount(cartCount > 0 ? cartCount - 1 : 0)
            }
          >
            Remove Item
          </button>

          <br /><br />

          <button onClick={logout}>
            Logout
          </button>
        </div>
      )}
    </div>
  )
}

export default App