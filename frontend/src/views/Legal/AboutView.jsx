import React from "react";
import { Container } from "../components/UI/UI";
import Card from "../components/UI/Card";
import {
	AboutHeader,
	AboutContent
} from "../components/About";

export default function AboutView() {
	return (
		<Container>
			<Card>
				<AboutHeader />
				<AboutContent />
			</Card>
		</Container>
	);
}
