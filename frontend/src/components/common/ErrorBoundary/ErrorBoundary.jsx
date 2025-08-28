
import React from "react";
import ErrorPageView from "@/pages/Core/ErrorPageView";

export default class ErrorBoundary extends React.Component {
	constructor(props) {
		super(props);
		this.state = { hasError: false };
	}

	static getDerivedStateFromError() {
		return { hasError: true };
	}

	componentDidCatch(error, info) {
		console.error("[ErrorBoundary]", error, info);
	}

	render() {
		if (this.state.hasError) {
			return <ErrorPageView />;
		}
		return this.props.children;
	}
}
