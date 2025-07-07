import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import useAppStore from "../store/useAppStore";
import { getRole } from "../api";

export default function useRequireAdmin() {
    const setIsAdmin = useAppStore((s) => s.setIsAdmin);
    const setIsLoading = useAppStore((s) => s.setIsLoading);
    const navigate = useNavigate();

    useEffect(() => {
        const verifyAdmin = async () => {
            try {
                const role = await getRole();
                if (!role.is_admin) {
                    throw new Error("Unauthorized");
                }
                setIsAdmin(true);
            } catch (err) {
                navigate("/admin");
            } finally {
                setIsLoading(false);
            }
        };

        verifyAdmin();
    }, [setIsAdmin, setIsLoading, navigate]);
}
