import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

    const { login } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    function handleSubmit(event) {
        event.preventDefault();

        const success = login(email, password);

        if (success) {
            const destination = location.state?.from?.pathname || "/dashboard";
            navigate(destination, { replace: true });
        } else {
            setError("Invalid email or password.");
        }
    }

    return (
        <div className="container">
            <h1>Login</h1>

            <form onSubmit={handleSubmit}>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    required
                />

                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    required
                />

                <button type="submit">Login</button>
            </form>

            {error && <p className="error">{error}</p>}

            <p>Demo email: admin@example.com</p>
            <p>Demo password: batman</p>
        </div>
    );
}