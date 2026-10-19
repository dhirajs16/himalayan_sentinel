"use client";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { Region } from "@/lib/types";
export default function Charts({ region }: { region: Region }) {
  const data = region.trend.map((risk, i) => ({
    day: `D${i + 1}`,
    risk,
    rain: region.rainfall_trend[i],
  }));
  return (
    <div className="chart">
      <div className="section-title">
        <div>
          <span className="eyebrow">7-day signal</span>
          <h3>Monitoring priority & rainfall</h3>
        </div>
        <span className="muted">Seeded demo data</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="risk" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#ff8668" stopOpacity={0.55} />
              <stop offset="1" stopColor="#ff8668" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="rain" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#62b8d5" stopOpacity={0.45} />
              <stop offset="1" stopColor="#62b8d5" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#263948" />
          <XAxis dataKey="day" stroke="#71828d" />
          <YAxis yAxisId="score" domain={[0, 100]} stroke="#405c53" label={{ value: "Score /100", angle: -90, position: "insideLeft" }} />
          <YAxis yAxisId="rain" orientation="right" stroke="#405c53" unit=" mm" />
          <Tooltip
            contentStyle={{
              background: "#122632",
              border: "1px solid #2b414e",
              borderRadius: 12,
            }}
          />
          <Area
            yAxisId="rain"
            type="monotone"
            dataKey="rain"
            name="Simulated rain (mm)"
            stroke="#62b8d5"
            fill="url(#rain)"
            isAnimationActive={false}
          />
          <Area
            yAxisId="score"
            type="monotone"
            dataKey="risk"
            name="Simulated monitoring score"
            stroke="#ff8668"
            fill="url(#risk)"
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
      <details><summary>Accessible simulated trend values</summary><table><thead><tr><th>Day</th><th>Score /100</th><th>Rainfall (mm)</th></tr></thead><tbody>{data.map(r => <tr key={r.day}><td>{r.day}</td><td>{r.risk}</td><td>{r.rain}</td></tr>)}</tbody></table></details>
    </div>
  );
}
