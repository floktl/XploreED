import { Listbox } from "@headlessui/react";
import { Check, ChevronDown } from "lucide-react";

export default function TopicMemoryFilters({
  filters,
  setFilters,
  grammarOptions,
  topicOptions,
  skillOptions,
  contextOptions,
  darkMode
}) {
  return (
    <tr>
      <th className="px-2 py-1 sticky top-[40px] bg-inherit">
        <Listbox value={filters.grammar} onChange={val => setFilters(f => ({ ...f, grammar: val }))}>
          <div className="relative w-full">
            <Listbox.Button title="Filter by grammar topic (e.g. verb, pronoun, tense)" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
              <span className="block truncate">{filters.grammar || "All"}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </span>
            </Listbox.Button>
            <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
              {grammarOptions.map(option => (
                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                      {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </div>
        </Listbox>
      </th>
      <th className="px-2 py-1 sticky top-[40px] bg-inherit">
        <Listbox value={filters.topic} onChange={val => setFilters(f => ({ ...f, topic: val }))}>
          <div className="relative w-full">
            <Listbox.Button title="Filter by lesson or context topic" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
              <span className="block truncate">{filters.topic || "All"}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </span>
            </Listbox.Button>
            <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
              {topicOptions.map(option => (
                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                      {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </div>
        </Listbox>
      </th>
      <th className="px-2 py-1 sticky top-[40px] bg-inherit">
        <Listbox value={filters.skill} onChange={val => setFilters(f => ({ ...f, skill: val }))}>
          <div className="relative w-full">
            <Listbox.Button title="Filter by skill type (e.g. gap-fill, initial, etc.)" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
              <span className="block truncate">{filters.skill || "All"}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </span>
            </Listbox.Button>
            <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
              {skillOptions.map(option => (
                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                      {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </div>
        </Listbox>
      </th>
      <th className="px-2 py-1 sticky top-[40px] bg-inherit" colSpan="5">
        <Listbox value={filters.context} onChange={val => setFilters(f => ({ ...f, context: val }))}>
          <div className="relative w-full">
            <Listbox.Button title="Filter by exercise context or theme" className="relative w-full cursor-pointer rounded bg-white dark:bg-gray-800 py-1 pl-2 pr-8 text-left border border-gray-300 dark:border-gray-700 text-xs">
              <span className="block truncate">{filters.context || "All"}</span>
              <span className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
                <ChevronDown className="w-4 h-4 text-gray-400" />
              </span>
            </Listbox.Button>
            <Listbox.Options className="absolute z-10 mt-1 max-h-48 w-full overflow-auto rounded bg-white dark:bg-gray-800 py-1 text-xs shadow-lg ring-1 ring-black/10 focus:outline-none">
              {contextOptions.map(option => (
                <Listbox.Option key={option} value={option} className={({ active }) => `cursor-pointer select-none py-1 pl-7 pr-2 ${active ? 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-white' : 'text-gray-900 dark:text-gray-100'}` }>
                  {({ selected }) => (
                    <>
                      <span className={`block truncate ${selected ? 'font-semibold' : 'font-normal'}`}>{option || "All"}</span>
                      {selected ? <span className="absolute left-1 top-1 flex items-center text-blue-600 dark:text-blue-300"><Check className="w-4 h-4" /></span> : null}
                    </>
                  )}
                </Listbox.Option>
              ))}
            </Listbox.Options>
          </div>
        </Listbox>
      </th>
    </tr>
  );
}
