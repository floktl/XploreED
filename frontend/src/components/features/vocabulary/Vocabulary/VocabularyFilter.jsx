import { Trash2 } from "lucide-react";
import Button from "../../../common/UI/Button";
import { Listbox } from "@headlessui/react";
import { Check, ChevronDown } from "lucide-react";

export default function VocabularyFilter({
  vocab,
  typeFilter,
  onTypeFilterChange,
  onDeleteAll,
  darkMode
}) {
  const getTypeOptions = () => {
    if (!vocab || !Array.isArray(vocab)) return [];
    const types = [...new Set(vocab.map(v => v.word_type).filter(Boolean))];
    return types.map(type => ({
      value: type,
      label: type.charAt(0).toUpperCase() + type.slice(1)
    }));
  };

  return (
    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
      <div className="flex-1">
        <Listbox value={typeFilter} onChange={onTypeFilterChange}>
          <div className="relative">
            <Listbox.Button className={`w-full cursor-pointer rounded-lg bg-white dark:bg-gray-800 py-2 pl-3 pr-10 text-left shadow-md border border-gray-300 dark:border-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-blue-400 transition text-base ${darkMode ? "text-white" : "text-gray-900"}`}>
              <span className="block truncate">
                {typeFilter || "All Types"}
              </span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDown className="h-5 w-5 text-gray-400" aria-hidden="true" />
              </span>
            </Listbox.Button>
            <Listbox.Options className={`absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md py-1 text-base shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none sm:text-sm ${darkMode ? "bg-gray-800" : "bg-white"}`}>
              <Listbox.Option
                className={({ active }) => `relative cursor-default select-none py-2 pl-10 pr-4 ${active ? (darkMode ? "bg-gray-700 text-white" : "bg-blue-100 text-blue-900") : (darkMode ? "text-gray-300" : "text-gray-900")}`}
                value=""
              >
                {({ selected }) => (
                  <>
                    <span className={`block truncate ${selected ? "font-medium" : "font-normal"}`}>
                      All Types
                    </span>
                    {selected ? (
                      <span className={`absolute inset-y-0 left-0 flex items-center pl-3 ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
                        <Check className="h-5 w-5" aria-hidden="true" />
                      </span>
                    ) : null}
                  </>
                )}
              </Listbox.Option>
              {getTypeOptions().map((type) => (
                <Listbox.Option
                  key={type.value}
                  className={({ active }) => `relative cursor-default select-none py-2 pl-10 pr-4 ${active ? (darkMode ? "bg-gray-700 text-white" : "bg-blue-100 text-blue-900") : (darkMode ? "text-gray-300" : "text-gray-900")}`}
                  value={type.value}
                >
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? "font-medium" : "font-normal"}`}>
                        {type.label}
                      </span>
                      {selected ? (
                        <span className={`absolute inset-y-0 left-0 flex items-center pl-3 ${darkMode ? "text-blue-400" : "text-blue-600"}`}>
                          <Check className="h-5 w-5" aria-hidden="true" />
                        </span>
                      ) : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </div>
        </Listbox>
      </div>
      {vocab && vocab.length > 0 && (
        <Button
          variant="danger"
          onClick={onDeleteAll}
          className="gap-2"
        >
          <Trash2 className="w-4 h-4" />
          Delete All
        </Button>
      )}
    </div>
  );
}
