import { useEffect, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#0088FE", "#FF8042"];

function SummaryRecap({ data }) {
  const [recap, setRecap] = useState({ purchase: 0, supply: 0 });

  useEffect(() => {
    if (data?.monetary_totals) {
      const { purchase, supply } = data.monetary_totals;
      setRecap({ purchase, supply });
    }
  }, [data]);

  const chartData = [
    { name: "Supply", value: recap.supply },
    { name: "Purchase", value: recap.purchase }
  ];

  const hasData = recap.purchase > 0 || recap.supply > 0;

  return (
    <div className="row row-cols-1 row-cols-md-2 g-4 mt-6">
      {/* First Card - Summary Recap */}
      <div className="col">
        <div className="card shadow-lg">
          <div className="card-body">
            <h5 className="card-title">Summary Recap</h5>
            <p className="card-text">
              Period: <strong>{data.start_date}</strong> to <strong>{data.end_date}</strong>
            </p>
            {data?.monetary_totals?.filters?.product && (
              <p className="card-text">
                Filtered by product: <strong>{data.monetary_totals.filters.product.name}</strong>
              </p>
            )}
            {data?.monetary_totals?.filters?.company && (
              <p className="card-text">
                Filtered by company: <strong>{data.monetary_totals.filters.company.name}</strong>
              </p>
            )}
            <div className="mt-4">
              <p><strong>Supply:</strong> ${recap.supply.toFixed(2)}</p>
              <p><strong>Purchase:</strong> ${recap.purchase.toFixed(2)}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Second Card - Pie Chart */}
      <div className="col">
        <div className="card shadow-lg">
          <div className="card-body">
            <h5 className="card-title">Monetary Distribution</h5>
            {hasData ? (
              <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  outerRadius={60}
                  dataKey="value"
                  label
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
            ) : (
              <p className="text-muted">No data available to visualize</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default SummaryRecap;


// {hasData ? (
//   <ResponsiveContainer width="100%" height={200}>
//     <PieChart>
//       <Pie
//         data={chartData}
//         cx="50%"
//         cy="50%"
//         outerRadius={60}
//         dataKey="value"
//         label
//       >
//         {chartData.map((entry, index) => (
//           <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
//         ))}
//       </Pie>
//       <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
//     </PieChart>
//   </ResponsiveContainer>
// ) : (
//   <p className="text-muted">No data available to visualize</p>
// )}