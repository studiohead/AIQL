import React from "react";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

type ChartType = "line" | "bar";

interface GenericGraphProps {
  data: any[];
  xKey: string;
  yKey: string;
  chartType?: ChartType;
  title?: string;
}

const GenericGraph: React.FC<GenericGraphProps> = ({
  data,
  xKey,
  yKey,
  chartType = "line",
  title = "Data Visualization",
}) => {
  return (
    <div style={{ width: "100%", height: 300, marginTop: 20 }}>
      <h3 style={{ color: "var(--color-text)" }}>{title}</h3>
      <ResponsiveContainer>
        {chartType === "line" ? (
          <LineChart data={data}>
            <Line
              type="monotone"
              dataKey={yKey}
              stroke="var(--color-primary)"
              strokeWidth={2}
              dot={{ stroke: "var(--color-primary-dark)", strokeWidth: 2 }}
              activeDot={{ r: 8 }}
            />
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis
              dataKey={xKey}
              stroke="var(--color-text)"
              tick={{ fontFamily: "var(--font-mono)" }}
            />
            <YAxis stroke="var(--color-text)" tick={{ fontFamily: "var(--font-mono)" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-bg)",
                borderColor: "var(--color-primary)",
                fontFamily: "var(--font-mono)",
                color: "var(--color-text)",
              }}
              itemStyle={{ color: "var(--color-primary)" }}
              cursor={{ stroke: "var(--color-primary)", strokeWidth: 2 }}
            />
          </LineChart>
        ) : (
          <BarChart data={data}>
            <Bar dataKey={yKey} fill="var(--color-primary)" />
            <CartesianGrid stroke="var(--color-border)" strokeDasharray="3 3" />
            <XAxis
              dataKey={xKey}
              stroke="var(--color-text)"
              tick={{ fontFamily: "var(--font-mono)" }}
            />
            <YAxis stroke="var(--color-text)" tick={{ fontFamily: "var(--font-mono)" }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "var(--color-bg)",
                borderColor: "var(--color-primary)",
                fontFamily: "var(--font-mono)",
                color: "var(--color-text)",
              }}
              itemStyle={{ color: "var(--color-primary)" }}
              cursor={{ fill: "var(--color-primary-dark)" }}
            />
          </BarChart>
        )}
      </ResponsiveContainer>
    </div>
  );
};

export default GenericGraph;
