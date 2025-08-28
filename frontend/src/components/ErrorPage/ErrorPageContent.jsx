import Button from "../common/UI/Button";
import { Container, Title } from "../common/UI/UI";

const ErrorPageContent = ({ onGoHome }) => {
	return (
		<Container>
			<Title>Something went wrong</Title>
			<p className="mb-4">An unexpected error occurred. Please try again.</p>
			<div className="text-center">
				<Button variant="link" onClick={onGoHome}>⬅️ Go Home</Button>
			</div>
		</Container>
	);
};

export default ErrorPageContent;
