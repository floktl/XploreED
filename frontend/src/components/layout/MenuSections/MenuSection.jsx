import { useNavigate } from "react-router-dom";
import Button from "../../common/UI/Button";
import Card from "../../common/UI/Card";
import { ChevronRight, ChevronDown } from "lucide-react";

export default function MenuSection({
	section,
	expandedSections,
	toggleSection,
	darkMode,
	getColorClasses
}) {
	const navigate = useNavigate();
	const isExpanded = expandedSections[section.id];
	const colors = getColorClasses(section.color);

	return (
		<Card className={`${colors.bg} ${colors.border} border transition-all duration-200`}>
			<div className="p-6">
				{/* Section Header */}
				<div
					className="flex items-center justify-between cursor-pointer mb-4"
					onClick={() => toggleSection(section.id)}
				>
					<div className="flex items-center gap-3">
						<div className={`p-2 rounded-lg ${colors.bg}`}>
							<section.icon className={`w-6 h-6 ${colors.icon}`} />
						</div>
						<div>
							<h3 className={`text-lg font-semibold ${colors.text}`}>
								{section.title}
							</h3>
						</div>
					</div>
					{isExpanded ? (
						<ChevronDown className={`w-5 h-5 ${colors.icon}`} />
					) : (
						<ChevronRight className={`w-5 h-5 ${colors.icon}`} />
					)}
				</div>

				{/* Section Items */}
				{isExpanded && (
					<div className="space-y-3">
						{section.items.map((item, index) => (
							<div
								key={index}
								className={`p-4 rounded-lg border transition-colors cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700/50 ${darkMode ? "border-gray-600 bg-gray-700/30" : "border-gray-200 bg-white"
									}`}
								onClick={() => navigate(item.path)}
							>
								<div className="flex items-center justify-between">
									<div className="flex items-center gap-3">
										<div className={`p-2 rounded-lg ${colors.bg}`}>
											<item.icon className={`w-5 h-5 ${colors.icon}`} />
										</div>
										<div>
											<h4 className={`font-medium ${colors.text}`}>
												{item.title}
											</h4>
											<p className={`text-sm ${colors.icon} mt-1`}>
												{item.description}
											</p>
										</div>
									</div>
									<div className="flex items-center gap-2">
										{item.notification && item.notification > 0 && (
											<span className="inline-flex items-center justify-center w-5 h-5 text-xs font-medium text-white bg-red-500 rounded-full">
												{item.notification}
											</span>
										)}
										<ChevronRight className={`w-4 h-4 ${colors.icon}`} />
									</div>
								</div>
							</div>
						))}
					</div>
				)}
			</div>
		</Card>
	);
}
