import React, { useState } from "react";
import { Container } from "../components/UI/UI";
import Card from "../components/UI/Card";
import {
	TermsHeader,
	TermsForm
} from "../components/TermsOfService";

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
