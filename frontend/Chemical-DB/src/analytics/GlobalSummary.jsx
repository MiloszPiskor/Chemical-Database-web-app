function formatChange(value) {
    if (value === null) return "N/A";
    if (value > 0) return `↑ ${value}%`;
    if (value < 0) return `↓ ${Math.abs(value)}%`;
    return "0%";
}