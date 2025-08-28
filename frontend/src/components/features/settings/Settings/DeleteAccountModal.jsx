import Modal from "../../../common/UI/Modal";
import Button from "../../../common/UI/Button";

export default function DeleteAccountModal({ onClose, onDeleteAll, onAnonymize }) {
	return (
		<Modal onClose={onClose}>
			<h2 className="text-lg font-bold mb-2">Delete Account</h2>
			<p className="mb-4">Would you like to delete all data or allow it to be anonymized for research?</p>
			<div className="flex justify-end gap-2">
				<Button variant="danger" onClick={onDeleteAll}>Delete All</Button>
				<Button variant="secondary" onClick={onAnonymize}>Anonymize</Button>
			</div>
		</Modal>
	);
}
