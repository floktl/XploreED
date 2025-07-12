import React, { useEffect, useState } from "react";
import ProgressRing from "./UI/ProgressRing";
import { useNavigate } from "react-router-dom";
import { getTopicMemory, clearTopicMemory, getTopicWeaknesses } from "../api";
import Button from "./UI/Button";
import Card from "./UI/Card";
import Alert from "./UI/Alert";
import Footer from "./UI/Footer";
import Badge from "./UI/Badge";
import Modal from "./UI/Modal";
import { Brain, ArrowLeft, Trash2 } from "lucide-react";
import { Container, Title, Input } from "./UI/UI";
import useAppStore from "../store/useAppStore";
import { Listbox } from "@headlessui/react";
import { Check, ChevronDown } from "lucide-react";

export default function TopicMemory() {
    const [topics, setTopics] = useState([]);
    const [showClear, setShowClear] = useState(false);
    const [error, setError] = useState("");
    const [weaknesses, setWeaknesses] = useState([]);
    const [filters, setFilters] = useState({
        grammar: "",
        topic: "",
        skill: "",
        context: "",
    });
    const [expandedCard, setExpandedCard] = useState(null);
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
            getTopicMemory()
                .then(setTopics)
                .catch((err) => {
                    console.error("Failed to load topic memory:", err);
                });
        }
    }, [username, isAdmin]);

    useEffect(() => {
        if (isAdmin) return;
        getTopicWeaknesses()
            .then(setWeaknesses)
            .catch((err) => {
                console.error("Failed to load weaknesses:", err);
            });
    }, [isAdmin]);

    const handleClear = async () => {
        try {
            await clearTopicMemory();
            setTopics([]);
            setWeaknesses([]);
            setShowClear(false);
            setError("");
        } catch (err) {
            console.error("Failed to clear topic memory:", err);
            setError("Could not clear topic memory.");
        }
    };

    // Compute unique filter options
    const grammarOptions = ["", ...Array.from(new Set(topics.map(t => t.grammar).filter(Boolean)))];
    const topicOptions = ["", ...Array.from(new Set(topics.map(t => t.topic).filter(Boolean)))];
    const skillOptions = ["", ...Array.from(new Set(topics.map(t => t.skill_type).filter(Boolean)))];
    const contextOptions = ["", ...Array.from(new Set(topics.map(t => t.context).filter(Boolean)))];

    // Filter logic: exact match or 'All'
    const filteredTopics = topics.filter((t) =>
        (filters.grammar === "" || t.grammar === filters.grammar) &&
        (filters.topic === "" || t.topic === filters.topic) &&
        (filters.skill === "" || t.skill_type === filters.skill) &&
        (filters.context === "" || t.context === filters.context)
    );
    //

    // Helper: interpolate color from red to yellow to green
    function getUrgencyColor(percent) {
        // 0 = red (#EF4444), 50 = yellow (#FACC15), 100 = green (#22C55E)
        if (percent <= 50) {
            // Red to yellow
            const ratio = percent / 50;
            return interpolateColor("#EF4444", "#FACC15", ratio);
        } else {
            // Yellow to green
            const ratio = (percent - 50) / 50;
            return interpolateColor("#FACC15", "#22C55E", ratio);
        }
    }
    // Simple hex color interpolation
    function interpolateColor(a, b, t) {
        const ah = a.replace('#', '');
        const bh = b.replace('#', '');
        const ar = parseInt(ah.substring(0,2), 16), ag = parseInt(ah.substring(2,4), 16), ab = parseInt(ah.substring(4,6), 16);
        const br = parseInt(bh.substring(0,2), 16), bg = parseInt(bh.substring(2,4), 16), bb = parseInt(bh.substring(4,6), 16);
        const rr = Math.round(ar + (br-ar)*t), rg = Math.round(ag + (bg-ag)*t), rb = Math.round(ab + (bb-ab)*t);
        return `#${rr.toString(16).padStart(2,'0')}${rg.toString(16).padStart(2,'0')}${rb.toString(16).padStart(2,'0')}`;
    }

    // Map ease_factor (1.3–2.5) to 0–100 for color
    function easeToPercent(ease) {
        const min = 1.3, max = 2.5;
        let p = ((ease - min) / (max - min)) * 100;
        p = Math.max(0, Math.min(100, p));
        return p;
    }

    return (
        <div className={`relative min-h-screen pb-20 overflow-x-hidden ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
            <Container >
                <Title>
                    <div className="flex items-center gap-2">
                        <Brain className="w-6 h-6" />
                        Topic Memory
                    </div>
                </Title>
                {weaknesses.length > 0 && (
                    <div className="mb-6 flex flex-col items-center gap-4">
                        <p className="text-sm">Biggest weaknesses</p>
                        <div className="flex gap-4">
                            {weaknesses.map((w) => (
                                <div key={w.grammar} className="flex flex-col items-center">
                                    <ProgressRing percentage={w.percent} size={70} color={getUrgencyColor(w.percent)} />
                                    <p className="mt-1 text-xs">{w.grammar}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {topics.length === 0 ? (
                    <Alert type="info">No topic memory saved yet.</Alert>
                ) : (
                    <>
                    {/* Desktop/tablet table view */}
                    <Card fit className="overflow-x-auto hidden sm:block">
                        <table className={`min-w-full border rounded-lg overflow-hidden ${darkMode ? "border-gray-600" : "border-gray-200"}`}>
                            <thead className={darkMode ? "bg-gray-700 text-gray-200" : "bg-blue-50 text-blue-700"} style={{position: 'sticky', top: 0, zIndex: 2}}>
                                <tr>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Grammar</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Topic</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Skill</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Context</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Ease</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Interval</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Next</th>
                                    <th className="px-4 py-2 text-left sticky top-0 bg-inherit">Reps</th>
                                </tr>
                                <tr>
                                    <th className="px-2 py-1 sticky top-[40px] bg-inherit">
                                        <Listbox value={filters.grammar} onChange={val => setFilters(f => ({ ...f, grammar: val }))}>
                                            <div className="relative w-full">
                                                <Listbox.Button title="Filter by grammar topic (e.g. verb, pronoun, tense)" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                                    <span className="block truncate">{filters.grammar || "All"}</span>
                                                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                                    </span>
                                                </Listbox.Button>
                                                <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                                    {grammarOptions.map(option => (
                                                        <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                            {({ selected }) => (
                                                                <>
                                                                    <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                                    {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                                </>
                                                            )}
                                                        </Listbox.Option>
                                                    ))}
                                                </Listbox.Options>
                                            </div>
                                        </Listbox>
                                    </th>
                                    <th className="px-2 py-1 sticky top-[40px] bg-inherit">
                                        <Listbox value={filters.topic} onChange={val => setFilters(f => ({ ...f, topic: val }))}>
                                            <div className="relative w-full">
                                                <Listbox.Button title="Filter by lesson or context topic" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                                    <span className="block truncate">{filters.topic || "All"}</span>
                                                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                                    </span>
                                                </Listbox.Button>
                                                <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                                    {topicOptions.map(option => (
                                                        <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                            {({ selected }) => (
                                                                <>
                                                                    <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                                    {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                                </>
                                                            )}
                                                        </Listbox.Option>
                                                    ))}
                                                </Listbox.Options>
                                            </div>
                                        </Listbox>
                                    </th>
                                    <th className="px-2 py-1 sticky top-[40px] bg-inherit">
                                        <Listbox value={filters.skill} onChange={val => setFilters(f => ({ ...f, skill: val }))}>
                                            <div className="relative w-full">
                                                <Listbox.Button title="Filter by skill type (e.g. gap-fill, initial, etc.)" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                                    <span className="block truncate">{filters.skill || "All"}</span>
                                                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                                    </span>
                                                </Listbox.Button>
                                                <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                                    {skillOptions.map(option => (
                                                        <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                            {({ selected }) => (
                                                                <>
                                                                    <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                                    {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                                </>
                                                            )}
                                                        </Listbox.Option>
                                                    ))}
                                                </Listbox.Options>
                                            </div>
                                        </Listbox>
                                    </th>
                                    <th className="px-2 py-1 sticky top-[40px] bg-inherit" colSpan="5">
                                        <Listbox value={filters.context} onChange={val => setFilters(f => ({ ...f, context: val }))}>
                                            <div className="relative w-full">
                                                <Listbox.Button title="Filter by exercise context or theme" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                                    <span className="block truncate">{filters.context || "All"}</span>
                                                    <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                        <ChevronDown className="w-4 h-4 text-gray-400" />
                                                    </span>
                                                </Listbox.Button>
                                                <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                                    {contextOptions.map(option => (
                                                        <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                            {({ selected }) => (
                                                                <>
                                                                    <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                                    {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                                </>
                                                            )}
                                                        </Listbox.Option>
                                                    ))}
                                                </Listbox.Options>
                                            </div>
                                        </Listbox>
                                    </th>
                                </tr>
                            </thead>
                            <tbody className={darkMode ? "bg-gray-900 divide-gray-700" : "bg-white divide-gray-200"}>
                                {filteredTopics.map((t) => (
                                    <tr key={t.id} className={darkMode ? "hover:bg-gray-700" : "hover:bg-gray-50"}>
                                        <td className="px-4 py-2 font-medium">{t.grammar || "-"}</td>
                                        <td className="px-4 py-2">{t.topic || "-"}</td>
                                        <td className={`px-4 py-2 ${darkMode ? "text-gray-300" : "text-gray-600"}`}>{t.skill_type}</td>
                                        <td className="px-4 py-2 whitespace-nowrap max-w-xs overflow-hidden text-ellipsis">{t.context}</td>
                                        <td className="px-4 py-2">{Number(t.ease_factor).toFixed(2)}</td>
                                        <td className="px-4 py-2">{t.intervall}</td>
                                        <td className="px-4 py-2">{t.next_repeat ? new Date(t.next_repeat).toLocaleDateString() : ""}</td>
                                        <td className="px-4 py-2">{t.repetitions}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </Card>
                    {/* Mobile card view */}
                    <div className="block sm:hidden space-y-3 mt-2">
                        {/* Sticky filter bar for mobile */}
                        <div className="sticky top-0 z-10 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 py-2 rounded-t-lg shadow-sm flex flex-wrap gap-2 px-2 mb-2">
                            <div className="w-[45%]">
                                <Listbox value={filters.grammar} onChange={val => setFilters(f => ({ ...f, grammar: val }))}>
                                    <div className="relative w-full">
                                        <Listbox.Button className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                            <span className="block truncate">{filters.grammar || "All"}</span>
                                            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                <ChevronDown className="w-4 h-4 text-gray-400" />
                                            </span>
                                        </Listbox.Button>
                                        <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                            {grammarOptions.map(option => (
                                                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                    {({ selected }) => (
                                                        <>
                                                            <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                            {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                        </>
                                                    )}
                                                </Listbox.Option>
                                            ))}
                                        </Listbox.Options>
                                    </div>
                                </Listbox>
                                <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 ml-1">Filter by grammar topic (e.g. verb, pronoun, tense)</div>
                            </div>
                            <div className="w-[45%]">
                                <Listbox value={filters.topic} onChange={val => setFilters(f => ({ ...f, topic: val }))}>
                                    <div className="relative w-full">
                                        <Listbox.Button className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                            <span className="block truncate">{filters.topic || "All"}</span>
                                            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                <ChevronDown className="w-4 h-4 text-gray-400" />
                                            </span>
                                        </Listbox.Button>
                                        <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                            {topicOptions.map(option => (
                                                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                    {({ selected }) => (
                                                        <>
                                                            <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                            {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                        </>
                                                    )}
                                                </Listbox.Option>
                                            ))}
                                        </Listbox.Options>
                                    </div>
                                </Listbox>
                                <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 ml-1">Filter by lesson or context topic</div>
                            </div>
                            <div className="w-[45%]">
                                <Listbox value={filters.skill} onChange={val => setFilters(f => ({ ...f, skill: val }))}>
                                    <div className="relative w-full">
                                        <Listbox.Button className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                            <span className="block truncate">{filters.skill || "All"}</span>
                                            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                <ChevronDown className="w-4 h-4 text-gray-400" />
                                            </span>
                                        </Listbox.Button>
                                        <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                            {skillOptions.map(option => (
                                                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                    {({ selected }) => (
                                                        <>
                                                            <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                            {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                        </>
                                                    )}
                                                </Listbox.Option>
                                            ))}
                                        </Listbox.Options>
                                    </div>
                                </Listbox>
                                <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 ml-1">Filter by skill type (e.g. gap-fill, initial, etc.)</div>
                            </div>
                            <div className="w-[45%]">
                                <Listbox value={filters.context} onChange={val => setFilters(f => ({ ...f, context: val }))}>
                                    <div className="relative w-full">
                                        <Listbox.Button className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
                                            <span className="block truncate">{filters.context || "All"}</span>
                                            <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                                                <ChevronDown className="w-4 h-4 text-gray-400" />
                                            </span>
                                        </Listbox.Button>
                                        <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
                                            {contextOptions.map(option => (
                                                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                                                    {({ selected }) => (
                                                        <>
                                                            <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                                                            {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                                                        </>
                                                    )}
                                                </Listbox.Option>
                                            ))}
                                        </Listbox.Options>
                                    </div>
                                </Listbox>
                                <div className="text-[11px] text-gray-500 dark:text-gray-400 mt-1 ml-1">Filter by exercise context or theme</div>
                            </div>
                        </div>
                        {filteredTopics.map((t) => (
                            <div
                                key={t.id}
                                className="rounded-xl border p-3 shadow bg-white dark:bg-gray-800 cursor-pointer transition-all"
                                style={{ borderColor: getUrgencyColor(easeToPercent(Number(t.ease_factor))) }}
                                onClick={() => setExpandedCard(expandedCard === t.id ? null : t.id)}
                            >
                                <div className="flex flex-wrap gap-2 text-xs mb-1">
                                    <span className="font-semibold text-blue-700 dark:text-blue-300">Grammar:</span> {t.grammar || "-"}
                                </div>
                                <div className="flex flex-wrap gap-2 text-xs mb-1">
                                    <span className="font-semibold text-blue-700 dark:text-blue-300">Topic:</span> {t.topic || "-"}
                                </div>
                                <div className="flex flex-wrap gap-2 text-xs mb-1">
                                    <span className="font-semibold text-blue-700 dark:text-blue-300">Skill:</span> {t.skill_type}
                                </div>
                                {expandedCard === t.id && (
                                    <>
                                        <div className="flex flex-wrap gap-2 text-xs mb-1">
                                            <span className="font-semibold text-blue-700 dark:text-blue-300">Context:</span> {t.context}
                                        </div>
                                        <div className="flex flex-wrap gap-2 text-xs mb-1">
                                            <span className="font-semibold text-blue-700 dark:text-blue-300">Ease:</span> {Number(t.ease_factor).toFixed(2)}
                                        </div>
                                        <div className="flex flex-wrap gap-2 text-xs mb-1">
                                            <span className="font-semibold text-blue-700 dark:text-blue-300">Interval:</span> {t.intervall}
                                        </div>
                                        <div className="flex flex-wrap gap-2 text-xs mb-1">
                                            <span className="font-semibold text-blue-700 dark:text-blue-300">Next:</span> {t.next_repeat ? new Date(t.next_repeat).toLocaleDateString() : ""}
                                        </div>
                                        <div className="flex flex-wrap gap-2 text-xs">
                                            <span className="font-semibold text-blue-700 dark:text-blue-300">Reps:</span> {t.repetitions}
                                        </div>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                    </>
                )}
                <div className="mt-6 flex justify-center gap-4">
                </div>
            </Container>
            <Footer>
                <Button size="md" variant="ghost" type="button" onClick={() => navigate("/menu")} className="gap-2">
                    <ArrowLeft className="w-4 h-4" />
                    Back
                </Button>
                    <Button variant="secondary" size="md" onClick={() => setFilters({ grammar: "", topic: "", skill: "", context: "" })}>
                        Reset Filters
                    </Button>
                    <Button variant="danger" size="md" onClick={() => setShowClear(true)} className="gap-2">
                        <Trash2 className="w-4 h-4" />
                        Clear Memory
                    </Button>
            </Footer>
            {showClear && (
                <Modal onClose={() => setShowClear(false)}>
                    <h2 className="text-lg font-bold mb-2">Delete Topic Memory</h2>
                    <p className="mb-4">Are you sure you want to delete all saved topic memory?</p>
                    {error && <Alert type="error" className="mb-2">{error}</Alert>}
                    <div className="flex justify-end gap-2">
                        <Button variant="danger" onClick={handleClear}>Delete</Button>
                        <Button variant="secondary" onClick={() => setShowClear(false)}>
                            Cancel
                        </Button>
                    </div>
                </Modal>
            )}
        </div>
    );
}
