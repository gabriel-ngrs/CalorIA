// Mock simplificado do Recharts para testes jsdom
const React = require("react");

const MockChart = ({ children }) => React.createElement("div", { "data-testid": "chart" }, children);
const MockPie = () => React.createElement("div", { "data-testid": "pie" });
const MockCell = () => null;
const MockBar = () => null;
const MockLine = () => null;
const MockXAxis = () => null;
const MockYAxis = () => null;
const MockTooltip = () => null;
const MockLegend = () => null;
const MockCartesianGrid = () => null;
const MockResponsiveContainer = ({ children }) =>
  React.createElement("div", { "data-testid": "responsive-container" }, children);

module.exports = {
  PieChart: MockChart,
  BarChart: MockChart,
  LineChart: MockChart,
  ResponsiveContainer: MockResponsiveContainer,
  Pie: MockPie,
  Cell: MockCell,
  Bar: MockBar,
  Line: MockLine,
  XAxis: MockXAxis,
  YAxis: MockYAxis,
  Tooltip: MockTooltip,
  Legend: MockLegend,
  CartesianGrid: MockCartesianGrid,
};
