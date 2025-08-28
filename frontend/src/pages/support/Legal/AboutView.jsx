import { Container } from "../../../components/common/UI/UI";
import Card from "../../../components/common/UI/Card";
import {
	AboutHeader,
	AboutContent
} from "../../../components/features/support/About";

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
