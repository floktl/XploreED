// src/components/LoginForm.jsx

import { useState } from 'react';
import { login, getProfile } from '../api/api';
import { useAppStore } from '../store/useAppStore';

export default function LoginForm() {
    const [username, setU] = useState('');
    const [password, setP] = useState('');
    const setUsername = useAppStore((s) => s.setUsername);

    const handleLogin = async () => {
        const result = await login(username, password);
        if (result.msg === 'Login successful') {
            const profile = await getProfile();
            setUsername(profile.msg);  // optional, can parse identity
        } else {
            alert(result.msg);
        }
    };

    return (
        <div className="p-4">
            <input type="text" value={username} onChange={(e) => setU(e.target.value)} placeholder="Username" />
            <input type="password" value={password} onChange={(e) => setP(e.target.value)} placeholder="Password" />
            <button onClick={handleLogin}>Login</button>
        </div>
    );
}
