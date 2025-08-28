import { ArrowLeft, ChevronLeft, ChevronRight } from "lucide-react";
import Button from "../../../common/UI/Button";
import Footer from "../../../common/UI/Footer";

export default function AIFeedbackFooter({ onNavigate, actions, exerciseNavigation }) {
	return (
		<Footer>
			<div className="flex justify-between items-center gap-2">
				{/* Back Button */}
				<Button
					size="sm"
					variant="ghost"
					type="button"
					onClick={() => onNavigate("/menu")}
					className="gap-1 rounded-full text-xs"
				>
					<ArrowLeft className="w-3 h-3" />
					Back
				</Button>

				{/* Exercise Navigation */}
				{exerciseNavigation && (
					<div className="flex gap-1">
						<Button
							size="sm"
							variant="secondary"
							onClick={exerciseNavigation.onPrevious}
							disabled={exerciseNavigation.disablePrev}
							className="gap-1 text-xs"
						>
							<ChevronLeft className="w-3 h-3" />
							Prev
						</Button>
						<Button
							size="sm"
							variant="secondary"
							onClick={exerciseNavigation.onNext}
							disabled={exerciseNavigation.disableNext}
							className="gap-1 text-xs"
						>
							Next
							<ChevronRight className="w-3 h-3" />
						</Button>
					</div>
				)}

				{/* Continue Button */}
				<div className="flex-shrink-0">
					{actions}
				</div>
			</div>
		</Footer>
	);
}
