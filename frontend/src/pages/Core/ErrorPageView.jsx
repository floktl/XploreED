// import { PageLayout } from "../../components/layout/index.ts";
// import { ErrorPageContent } from "../../components/ErrorPage/index.js";

export default function ErrorPage() {
	    return (
        <div>
            <h1>Error Page</h1>
            <button onClick={() => window.location.assign("/")}>Go Home</button>
        </div>
    );
}
