import React from "react";
import MenuSection from "./MenuSection";

export default function MenuGrid({
  menuSections,
  expandedSections,
  onToggleSection,
  onNavigate,
  darkMode
}) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {menuSections.map((section) => (
        <MenuSection
          key={section.id}
          section={section}
          isExpanded={expandedSections[section.id]}
          onToggle={onToggleSection}
          onNavigate={onNavigate}
          darkMode={darkMode}
        />
      ))}
    </div>
  );
}
