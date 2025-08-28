import { useState } from "react";
import { Container } from "../../../components/common/UI/UI";
import Card from "../../../components/common/UI/Card";
import {
	TermsHeader,
	TermsForm
} from "../../../components/features/support/TermsOfService";

export default function TermsOfServiceView() {
	const [agreed, setAgreed] = useState(false);

	const handleSubmit = (e) => {
		e.preventDefault();
		if (!agreed) {
			alert("Please agree to the terms to continue.");
			return;
		}
		alert("Thank you for subscribing!");
	};

	return (
		<Container>
			<Card>
				<TermsHeader />
				<TermsForm
					agreed={agreed}
					setAgreed={setAgreed}
					onSubmit={handleSubmit}
				/>
			</Card>
		</Container>
	);
}
