import { useEffect, useState } from "react";
import { Card } from "react-bootstrap";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from "recharts";

const dummyBarData = [
  { name: "Hydrochloric", usage: 240 },
  { name: "Sodium", usage: 180 },
  { name: "Ethanol", usage: 300 },
  { name: "Acetone", usage: 200 },
  { name: "Methanol", usage: 270 },
];

const dummyLineData = [
  { month: "Jan", usage: 120 },
  { month: "Feb", usage: 180 },
  { month: "Mar", usage: 150 },
  { month: "Apr", usage: 220 },
  { month: "May", usage: 260 },
  { month: "Jun", usage: 300 },
];

const dummyPieData = [
  { name: "Solvents", value: 400 },
  { name: "Acids", value: 300 },
  { name: "Bases", value: 300 },
  { name: "Salts", value: 200 },
];

const COLORS = ["#0088FE", "#00C49F", "#FFBB28", "#FF8042"];

export default function AnalyticsProductsPage() {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const delay = setTimeout(() => setLoading(false), 1000); // Simulate load
    return () => clearTimeout(delay);
  }, []);

  if (loading) {
    return (
      <div className="d-flex justify-content-center align-items-center flex-column" style={{ height: "100vh" }}>
        <div className="spinner-border text-info" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-3 text-info fs-4">Loading analytics...</p>
      </div>
    );
  }

  return (
    <div className="container mt-5">
      <h2 className="mb-4">Product Analytics</h2>

      <Card className="mb-4 p-3 shadow">
        <h4 className="mb-3">Most Used Chemicals</h4>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={dummyBarData}>
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="usage" fill="#8884d8" />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      <Card className="mb-4 p-3 shadow">
        <h4 className="mb-3">Monthly Usage Trend</h4>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={dummyLineData}>
            <XAxis dataKey="month" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="usage" stroke="#82ca9d" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </Card>

      <Card className="mb-4 p-3 shadow">
        <h4 className="mb-3">Category Distribution</h4>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={dummyPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100}>
              {dummyPieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </Card>
    </div>
  );
}
