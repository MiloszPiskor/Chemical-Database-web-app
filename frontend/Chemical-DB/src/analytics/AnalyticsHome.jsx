import React from "react";
import { Link } from "react-router-dom";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts"; // Example chart
import { Container, Row, Col, Card, Button } from "react-bootstrap";

// Sample mock data
const data = [
  { name: "Satisfaction", value: 100 },
  { name: "Neutral", value: 0 },
  { name: "Dissatisfaction", value: 0 },
];

const COLORS = ["#4CAF50", "#FFEB3B", "#F44336"]; // Green, Yellow, Red for pie chart

function AnalyticsHome() {
  return (
    <Container className="my-5">
      <Row className="mb-4">
        <Col>
          <h1>Welcome to Analytics!</h1>
          <p>
            This section of the app is dedicated to providing you with insightful
            analytics and trends based on your data. Here, you will be able to track,
            analyze, and visualize key metrics, such as sales, purchases, satisfaction,
            and more.
          </p>
          <p>
            Whether you're tracking your team's performance or analyzing trends over time,
            this page will give you an overview of the amazing insights you'll be able to
            explore in the upcoming sections.
          </p>
        </Col>
      </Row>

      <Row>
        <Col md={6}>
          <Card className="mb-4">
            <Card.Body>
              <Card.Title>Current Satisfaction: 100%</Card.Title>
              <div style={{ width: '100%', height: 300 }}>
              <ResponsiveContainer>
              <PieChart>
                <Pie
                  data={data}
                  dataKey="value"
                  nameKey="name"
                  outerRadius={80}
                  fill="#8884d8"
                  label
                >
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
              </ResponsiveContainer>
              </div>
              <p>We're doing great! 100% satisfaction! 🎉</p>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card className="mb-4">
            <Card.Body>
              <Card.Title>Upcoming Analysis Features</Card.Title>
              <ul>
                <li>Sales Performance</li>
                <li>Customer Satisfaction Trends</li>
                <li>Purchase & Supply Overview</li>
                <li>Product Performance</li>
              </ul>
              <Button variant="primary" as={Link} to="/analytics/sales">
                Explore Sales Data
              </Button>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mt-5">
        <Col>
          <h2>What to Expect:</h2>
          <ul>
            <li>
              <strong>Sales Analytics:</strong> See how your sales are performing over time.
            </li>
            <li>
              <strong>Trends & Comparisons:</strong> Visualize key trends in your business.
            </li>
            <li>
              <strong>Performance Tracking:</strong> Keep track of product and company performance.
            </li>
          </ul>
        </Col>
      </Row>
    </Container>
  );
}

export default AnalyticsHome;
