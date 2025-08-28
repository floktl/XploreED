import { useState } from "react";
import Button from "../../../../common/UI/Button";
import { Input } from "../../../../common/UI/UI";
import { Eye, EyeOff, LogIn } from "lucide-react";

export default function LoginForm({
    name,
    setName,
    password,
    setPassword,
    showPassword,
    setShowPassword,
    isLoading,
    onSubmit,
    onSwitchToSignup
}) {
    return (
        <div className="space-y-4">
            <div>
                <label htmlFor="username" className="block text-sm font-medium mb-2">
                    Username
                </label>
                <Input
                    id="username"
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="Enter your username"
                    disabled={isLoading}
                    className="w-full"
                />
            </div>

            <div>
                <label htmlFor="password" className="block text-sm font-medium mb-2">
                    Password
                </label>
                <div className="relative">
                    <Input
                        id="password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter your password"
                        disabled={isLoading}
                        className="w-full pr-10"
                    />
                    <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                        disabled={isLoading}
                    >
                        {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                </div>
            </div>

            <Button
                type="submit"
                onClick={onSubmit}
                disabled={isLoading}
                className="w-full gap-2"
            >
                <LogIn className="w-4 h-4" />
                {isLoading ? "Logging in..." : "Log In"}
            </Button>

            <div className="text-center">
                <button
                    type="button"
                    onClick={onSwitchToSignup}
                    className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    disabled={isLoading}
                >
                    Don't have an account? Sign up
                </button>
            </div>
        </div>
    );
}
