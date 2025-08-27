import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Container } from "../components/UI/UI";
import Alert from "../components/UI/Alert";
import Modal from "../components/UI/Modal";
import Button from "../components/UI/Button";
import ReportVocabModal from "../components/ReportVocabModal";
import useAppStore from "../store/useAppStore";
import { getVocabulary, deleteVocab, reportVocab, deleteAllVocab } from "../api";
import {
	VocabularyHeader,
	VocabularyFilter,
	VocabularyList,
	VocabularyFooter,
	VocabularyModal
} from "../components/Vocabulary";

export default function VocabularyView() {
	const [vocab, setVocab] = useState([]);
	const [selected, setSelected] = useState(null);
	const [showReport, setShowReport] = useState(false);
	const [showDeleteAll, setShowDeleteAll] = useState(false);
	const [typeFilter, setTypeFilter] = useState("");

	const username = useAppStore((state) => state.username);
	const setUsername = useAppStore((state) => state.setUsername);
	const darkMode = useAppStore((state) => state.darkMode);
	const isAdmin = useAppStore((state) => state.isAdmin);
	const navigate = useNavigate();
	const isLoading = useAppStore((state) => state.isLoading);
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
	}, [isAdmin, username, setUsername, navigate, isLoading]);

	useEffect(() => {
		if (!isAdmin) {
			getVocabulary()
				.then((data) => {
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

	const handleDeleteAll = () => {
		setShowDeleteAll(true);
	};

	const confirmDeleteAll = async () => {
		try {
			await deleteAllVocab();
			setVocab([]);
			setShowDeleteAll(false);
		} catch (err) {
			console.error('Failed to delete all vocab', err);
		}
	};

	return (
		<div className={`relative min-h-screen pb-20 ${darkMode ? "bg-gray-900 text-white" : "bg-white text-gray-800"}`}>
			<Container>
				<VocabularyHeader onNavigate={navigate} darkMode={darkMode} />
				<VocabularyFilter
					vocab={vocab}
					typeFilter={typeFilter}
					onTypeFilterChange={setTypeFilter}
					onDeleteAll={handleDeleteAll}
					darkMode={darkMode}
				/>
				<VocabularyList
					vocab={vocab}
					typeFilter={typeFilter}
					onVocabSelect={setSelected}
					darkMode={darkMode}
				/>
			</Container>

			<VocabularyFooter onNavigate={navigate} />

			<VocabularyModal
				selected={selected}
				onClose={() => setSelected(null)}
				onForget={handleForget}
				onShowReport={() => setShowReport(true)}
			/>

			{selected && showReport && (
				<ReportVocabModal
					vocab={selected}
					onSend={handleSendReport}
					onClose={() => setShowReport(false)}
				/>
			)}

			{showDeleteAll && (
				<Modal onClose={() => setShowDeleteAll(false)}>
					<h2 className="text-xl font-semibold mb-4">Delete All Vocabulary</h2>
					<p className="mb-4">Are you sure you want to delete all your vocabulary? This action cannot be undone.</p>
					<div className="flex justify-end gap-2">
						<Button variant="secondary" onClick={() => setShowDeleteAll(false)}>
							Cancel
						</Button>
						<Button variant="danger" onClick={confirmDeleteAll}>
							Delete All
						</Button>
					</div>
				</Modal>
			)}
		</div>
	);
}
