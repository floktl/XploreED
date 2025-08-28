import Button from "../../../../common/UI/Button";
import { Input } from "../../../../common/UI/UI";
import { Eye, EyeOff, UserPlus } from "lucide-react";

export default function SignupForm({
    name,
    setName,
    password,
    setPassword,
    confirmPassword,
    setConfirmPassword,
    showPassword,
    setShowPassword,
    isLoading,
    onSubmit,
    onSwitchToLogin,
    passwordStrength
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
                    placeholder="Choose a username"
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
                        placeholder="Choose a password"
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
                {password && (
                    <div className="mt-1 text-xs">
                        <span className={`${
                            passwordStrength === "Weak" ? "text-red-500" :
                            passwordStrength === "Moderate" ? "text-yellow-500" :
                            "text-green-500"
                        }`}>
                            Strength: {passwordStrength}
                        </span>
                    </div>
                )}
            </div>

            <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium mb-2">
                    Confirm Password
                </label>
                <Input
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm your password"
                    disabled={isLoading}
                    className="w-full"
                />
            </div>

            <Button
                type="submit"
                onClick={onSubmit}
                disabled={isLoading}
                className="w-full gap-2"
            >
                <UserPlus className="w-4 h-4" />
                {isLoading ? "Creating account..." : "Sign Up"}
            </Button>

            <div className="text-center">
                <button
                    type="button"
                    onClick={onSwitchToLogin}
                    className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
                    disabled={isLoading}
                >
                    Already have an account? Log in
                </button>
            </div>
        </div>
    );
}
