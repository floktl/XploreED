import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "./UI/Button";
import { Container, Title } from "./UI/UI";
import { BookOpen, Target, ArrowLeft, Info, Trash2 } from "lucide-react";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Modal from "./UI/Modal";
import ReportVocabModal from "./ReportVocabModal";
import { getVocabulary, deleteVocab, reportVocab, deleteAllVocab } from "../api";
import useAppStore from "../store/useAppStore";
import useMediaQuery from "../utils/useMediaQuery";
import { Listbox } from "@headlessui/react";
import { Check, ChevronDown } from "lucide-react";

export default function Vocabulary() {
    const [vocab, setVocab] = useState([]);
    const [selected, setSelected] = useState(null);
    const [showReport, setShowReport] = useState(false);
    const [showDeleteAll, setShowDeleteAll] = useState(false);
    const username = useAppStore((state) => state.username);
    const setUsername = useAppStore((state) => state.setUsername);
    const darkMode = useAppStore((state) => state.darkMode);
    const isAdmin = useAppStore((state) => state.isAdmin);
    const navigate = useNavigate();
    const isLoading = useAppStore((state) => state.isLoading);
    const isMobile = useMediaQuery("(max-width: 640px)");
    const [typeFilter, setTypeFilter] = useState("");
    const setCurrentPageContent = useAppStore((s) => s.setCurrentPageContent);
    const clearCurrentPageContent = useAppStore((s) => s.clearCurrentPageContent);

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
                .then((data) => {
                    // Ensure data is always an array
                    if (Array.isArray(data)) {
                        setVocab(data);
                    } else if (data && Array.isArray(data.vocabulary)) {
                        setVocab(data.vocabulary);
                    } else {
                        console.warn("Unexpected vocabulary data format:", data);
                        setVocab([]);
                    }
                })
                .catch((err) => {
                    console.error("Failed to load vocabulary:", err);
                    setVocab([]);
                });
        }
    }, [username, isAdmin]);

    useEffect(() => {
        setCurrentPageContent({
            type: "vocabulary",
            username,
            vocab
        });
        return () => clearCurrentPageContent();
    }, [username, vocab, setCurrentPageContent, clearCurrentPageContent]);

    const handleForget = async (vocabEntry = null) => {
        const entry = vocabEntry || selected;
        if (!entry) return;
        try {
            await deleteVocab(entry.id);
            setVocab((v) => v.filter((w) => w.id !== entry.id));
            if (!vocabEntry) setSelected(null);
        } catch (err) {
            console.error('Failed to delete vocab', err);
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

    const handleDeleteClick = (vocabEntry, e) => {
        e.stopPropagation();
        setSelected(vocabEntry);
        handleForget(vocabEntry);
    };

    // Compute unique types for dropdown
    const vocabTypes = Array.from(new Set((vocab || []).map(v => v.word_type).filter(Boolean)));
    const filteredVocab = typeFilter ? (vocab || []).filter(v => v.word_type === typeFilter) : (vocab || []);

    const typeOptions = [
        { value: "", label: "All" },
        ...vocabTypes.map(type => ({ value: type, label: type.charAt(0).toUpperCase() + type.slice(1) }))
    ];

    return (
        <div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container>
                <Title>
                    <div className="flex items-center gap-2">
                        <BookOpen className="w-6 h-6" />
                        <span>My Vocabulary</span>
                    </div>
                </Title>
                {/* Vocab type filter */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
                    <div className="flex-1">
                        <Listbox value={typeFilter} onChange={setTypeFilter}>
                            <div className="relative w-full">
                                <Listbox.Button className="relative w-full cursor-pointer rounded-lg bg-white dark:bg-gray-800 py-2 pl-3 pr-10 text-left shadow-md border border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition text-base">
                                    <span className="block truncate">{typeOptions.find(o => o.value === typeFilter)?.label}</span>
                                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
                                        <ChevronDown className="w-5 h-5 text-gray-400" />
                                    </span>
                                </Listbox.Button>
                                <Listbox.Options className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-lg bg-white dark:bg-gray-800 py-1 text-base shadow-lg ring-1 ring-black/10 focus:outline-none">
                                    {typeOptions.map(option => (
                                        <Listbox.Option
                                            key={option.value}
                                            value={option.value}
                                            className={({ active }) =>
                                                `relative cursor-pointer select-none py-2 pl-10 pr-4 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}`
                                            }
                                        >
                                            {({ selected }) => (
                                                <>
                                                    <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option.label}</span>
                                                    {selected ? (
                                                        <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-blue-600 dark:text-blue-300">
                                                            <Check className="w-5 h-5" />
                                                        </span>
                                                    ) : null}
                                                </>
                                            )}
                                        </Listbox.Option>
                                    ))}
                                </Listbox.Options>
                            </div>
                        </Listbox>
                    </div>
                    {(vocab || []).length > 0 && (
                        <Button variant="danger" onClick={() => setShowDeleteAll(true)}>
                            <Trash2 className="w-4 h-4 mr-2" /> Delete All
                        </Button>
                    )}
                </div>
                {showDeleteAll && (
                    <Modal onClose={() => setShowDeleteAll(false)}>
                        <h2 className="text-lg font-bold mb-2">Delete All Vocabulary</h2>
                        <p>Are you sure you want to delete <strong>ALL</strong> vocabulary? This cannot be undone.</p>
                        <div className="flex justify-end gap-2 mt-4">
                            <Button variant="secondary" onClick={() => setShowDeleteAll(false)}>Cancel</Button>
                            <Button variant="danger" onClick={async () => {
                                await deleteAllVocab();
                                setVocab([]);
                                setShowDeleteAll(false);
                            }}>Delete All</Button>
                        </div>
                    </Modal>
                )}

                {filteredVocab.length === 0 ? (
                    <Alert type="info" className="flex items-center gap-2">
                        <Info className="w-4 h-4" />
                        <span>No vocabulary saved yet. Try completing a few translations or levels!</span>
                    </Alert>
                ) : (
                    <Card fit className="p-0">
                        {isMobile ? (
                            <div className="flex flex-col gap-3">
                                {filteredVocab.map((v, i) => (
                                    <div
                                        key={i}
                                        className={`rounded-lg border ${darkMode ? "border-gray-700 bg-gray-900" : "border-gray-200 bg-white"} p-3 shadow-sm flex flex-col gap-1 relative cursor-pointer transition hover:shadow-md`}
                                        onClick={() => setSelected(v)}
                                    >
                                        <div className="flex items-center justify-between">
                                            <div className="font-bold text-lg">{v.vocab}</div>
                                        </div>
                                        {v.article && <div className="text-xs text-blue-700 font-semibold">{v.article}</div>}
                                        <div className="text-sm"><span className="font-semibold">Translation:</span> {v.translation}</div>
                                        <div className="text-sm"><span className="font-semibold">Type:</span> {v.word_type}</div>
                                        {v.next_review && <div className="text-xs text-gray-500">Due: {new Date(v.next_review).toLocaleDateString()}</div>}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="w-full rounded-lg overflow-x-auto">
                                <table className={`min-w-full border-separate border-spacing-0 ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                                    <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"}>
                                        <tr>
                                            <th className="sticky left-0 z-10 bg-inherit px-4 py-2 text-left">German Word</th>
                                            <th className="px-4 py-2 text-left">Article</th>
                                            <th className="px-4 py-2 text-left">English Translation</th>
                                            <th className="px-4 py-2 text-left">Type</th>
                                            <th className="px-4 py-2 text-left">Due</th>
                                            <th className="px-2 py-2"></th>
                                        </tr>
                                    </thead>
                                    <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                                        {filteredVocab.map((v, i) => (
                                            <tr key={i} className={darkMode ? "hover:bg-gray-700 cursor-pointer" : "hover:bg-gray-50 cursor-pointer"} onClick={() => setSelected(v)}>
                                                <td className="sticky left-0 z-10 bg-inherit px-4 py-2 font-medium">{v.vocab}</td>
                                                <td className="px-4 py-2">{v.article || ""}</td>
                                                <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{v.translation}</td>
                                                <td className="px-4 py-2 capitalize">{v.word_type || ""}</td>
                                                <td className="px-4 py-2">{v.next_review ? new Date(v.next_review).toLocaleDateString() : ""}</td>
                                                <td className="px-2 py-2">
                                                    {/* Removed delete button from table row */}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </Card>
                )}

            </Container>

            <Footer>
                <Button
                    size="md"
                    variant="ghost"
                    type="button"
                    onClick={() => navigate("/menu")}
                    className="gap-2"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </Button>

                <Button
                    variant="primary"
                    onClick={() => navigate("/vocab-trainer")}
                    className="gap-2"
                >
                    <Target className="w-4 h-4" />
                    Train Vocabulary
                </Button>
            </Footer>
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
                        <Button variant="danger" onClick={() => handleForget(selected)}>Forget</Button>
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
