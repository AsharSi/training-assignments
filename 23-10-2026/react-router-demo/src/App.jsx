import { BrowserRouter, Routes, Route, Link } from "react-router-dom"
import Home from "./Home"
import Products from "./Products"
import About from "./About"

function App() {

  return (
    <>
      <BrowserRouter>
        <div style={{display: "flex", gap: "20px"}}>
          <Link to="/">
            Home
          </Link>
          {" | "}
          <Link to="/products">
            Products
          </Link>
          {" | "}
          <Link to="/about">
            About
          </Link>
        </div>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </BrowserRouter>
    </>
  )
}

export default App
