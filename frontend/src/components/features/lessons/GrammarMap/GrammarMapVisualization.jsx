
const NODE_SIZE = 80;
const GAP = 40;
const COLS = 5;

export default function GrammarMapVisualization({ nodes, darkMode }) {
  const width = COLS * (NODE_SIZE + GAP) + GAP;
  const rows = Math.ceil(nodes.length / COLS);
  const height = rows * (NODE_SIZE + GAP) + GAP;

  return (
    <div className="overflow-auto border rounded" style={{ height: "70vh" }}>
      <svg width={width} height={height} className="bg-gray-100 dark:bg-gray-800">
        {nodes.map((n, idx) => {
          const col = idx % COLS;
          const row = Math.floor(idx / COLS);
          const x = GAP + col * (NODE_SIZE + GAP);
          const y = GAP + row * (NODE_SIZE + GAP);
          const opacity = Math.min(1, Math.max(0.2, n.avgQuality / 5));
          const nextIdx = idx + 1;
          const nextCol = nextIdx % COLS;
          const nextRow = Math.floor(nextIdx / COLS);
          const nextX = GAP + nextCol * (NODE_SIZE + GAP) + NODE_SIZE / 2;
          const nextY = GAP + nextRow * (NODE_SIZE + GAP) + NODE_SIZE / 2;
          return (
            <g key={n.grammar}>
              {idx < nodes.length - 1 && (
                <line
                  x1={x + NODE_SIZE / 2}
                  y1={y + NODE_SIZE / 2}
                  x2={nextX}
                  y2={nextY}
                  stroke="#60a5fa"
                  strokeWidth={2}
                />
              )}
              <rect
                x={x}
                y={y}
                width={NODE_SIZE}
                height={NODE_SIZE}
                rx={10}
                fill={`rgba(59,130,246,${opacity})`}
                stroke="#1d4ed8"
              />
              <text
                x={x + NODE_SIZE / 2}
                y={y + NODE_SIZE / 2}
                textAnchor="middle"
                dominantBaseline="central"
                fontSize="12"
                fill={darkMode ? "white" : "#1e3a8a"}
              >
                {n.grammar}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
