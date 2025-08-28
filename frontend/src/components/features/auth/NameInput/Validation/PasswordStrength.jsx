
export default function PasswordStrength({ password }) {
    const getPasswordStrength = (pw) => {
        if (!pw) return "";
        if (pw.length < 6) return "Weak";
        if (pw.match(/[A-Z]/) && pw.match(/[0-9]/) && pw.length >= 8)
            return "Strong";
        return "Moderate";
    };

    const strength = getPasswordStrength(password);

    if (!password) return null;

    return (
        <div className="mt-1 text-xs">
            <span className={`${
                strength === "Weak" ? "text-red-500" :
                strength === "Moderate" ? "text-yellow-500" :
                "text-green-500"
            }`}>
                Strength: {strength}
            </span>
        </div>
    );
}
