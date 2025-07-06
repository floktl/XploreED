import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import { BookOpen, Target, ArrowLeft, Info } from "lucide-react";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Modal from "./UI/Modal";
import ReportVocabModal from "./ReportVocabModal";
import { getVocabulary, deleteVocab, reportVocab } from "../api";
import useAppStore from "../store/useAppStore";

export default function Vocabulary() {
    const [vocab, setVocab] = useState([]);
    const [selected, setSelected] = useState(null);
    const [showReport, setShowReport] = useState(false);
    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const navigate = useNavigate();
    const isLoading = useAppStore((state) => state.isLoading);

    useEffect(() => {
        const storedUsername = localStorage.getItem("username");
        if (!username && storedUsername) {
            setUsername(storedUsername);
        }

        if (!isLoading && (!username || isAdmin)) {
            navigate(isAdmin ? "/admin-panel" : "/");
        }
    }, [isAdmin, username, setUsername, navigate]);

    useEffect(() => {
        if (!isAdmin) {
            getVocabulary()
                .then(setVocab)
                .catch((err) => {
                    console.error("Failed to load vocabulary:", err);
                });
        }
    }, [username, isAdmin]);

    const handleForget = async () => {
        if (!selected) return;
        try {
            await deleteVocab(selected.id);
            setVocab((v) => v.filter((w) => w.id !== selected.id));
            setSelected(null);
        } catch (err) {
            console.error("Failed to delete vocab", err);
        }
    };

    const handleSendReport = async (message) => {
        if (!selected) return;
        try {
            await reportVocab(selected.id, message);
            setShowReport(false);
        } catch (err) {
            console.error("Failed to report vocab", err);
        }
    };

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container
                bottom={
                    <Button size="md" variant="ghost" type="button" onClick={() => navigate("/profile")} className="gap-2">
                        <ArrowLeft className="w-4 h-4" />
                        Back to Profile
                    </Button>
                }
            >
                <Title>
                    <div className="flex items-center gap-2">
                        <BookOpen className="w-6 h-6" />
                        <span>My Vocabulary</span>
                    </div>
                </Title>

                <div className="mb-4 text-center">
                    <Button onClick={() => navigate("/vocab-trainer")} className="gap-2">
                        <Target className="w-4 h-4" />
                        Train Vocabulary
                    </Button>
                </div>

                {vocab.length === 0 ? (
                    <Alert type="info" className="flex items-center gap-2">
                        <Info className="w-4 h-4" />
                        <span>No vocabulary saved yet. Try completing a few translations or levels!</span>
                    </Alert>
                ) : (
                    <Card fit className="p-0 overflow-x-auto">
                        <div className="w-full rounded-lg">
                            <table className={`min-w-full border-separate border-spacing-0 ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                                <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                    <tr>
                                        <th className="sticky left-0 z-10 bg-inherit px-4 py-2 text-left">German Word</th>
                                        <th className="px-4 py-2 text-left">Article</th>
                                        <th className="px-4 py-2 text-left">English Translation</th>
                                        <th className="px-4 py-2 text-left">Type</th>
                                        <th className="px-4 py-2 text-left">Due</th>
                                    </tr>
                                </thead>
                                <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                                    {vocab.map((v, i) => (
                                        <tr key={i} className={darkMode ? "hover:bg-gray-700 cursor-pointer" : "hover:bg-gray-50 cursor-pointer"} onClick={() => setSelected(v)}>
                                            <td className="sticky left-0 z-10 bg-inherit px-4 py-2 font-medium">{v.vocab}</td>
                                            <td className="px-4 py-2">{v.article || ""}</td>
                                            <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{v.translation}</td>
                                            <td className="px-4 py-2 capitalize">{v.word_type || ""}</td>
                                            <td className="px-4 py-2">{v.next_review ? new Date(v.next_review).toLocaleDateString() : ""}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </Card>
                )}

            </Container>

            <Footer />

            {selected && (
                <Modal onClose={() => setSelected(null)}>
                    <h2 className="text-xl font-semibold mb-4">
                        {selected.article ? `${selected.article} ${selected.vocab}` : selected.vocab}
                    </h2>
                    <p className="mb-2"><strong>Translation:</strong> {selected.translation}</p>
                    {selected.details && (<p className="mb-2"><strong>Info:</strong> {selected.details}</p>)}
                    {selected.word_type && (<p className="mb-2 capitalize"><strong>Type:</strong> {selected.word_type}</p>)}
                    {selected.created_at && (<p className="mb-2"><strong>Learned:</strong> {new Date(selected.created_at).toLocaleString()}</p>)}
                    {selected.next_review && (<p className="mb-2"><strong>Next review:</strong> {new Date(selected.next_review).toLocaleDateString()}</p>)}
                    {selected.context && (<p className="mb-2"><strong>Context:</strong> {selected.context}</p>)}
                    {selected.exercise && (<p className="mb-2"><strong>Exercise:</strong> {selected.exercise}</p>)}
                    <div className="flex justify-end gap-2 mt-4">
                        <Button variant="danger" onClick={handleForget}>Forget</Button>
                        <Button variant="secondary" onClick={() => setShowReport(true)}>Report</Button>
                    </div>
                </Modal>
            )}

            {selected && showReport && (
                <ReportVocabModal
                    vocab={selected}
                    onSend={handleSendReport}
                    onClose={() => setShowReport(false)}
                />
            )}
        </div>
    );
}
