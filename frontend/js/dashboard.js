const backBtn = document.getElementById("backBtn");

if (backBtn) {
  backBtn.addEventListener("click", () => {
    window.location.href = "index.html";
  });
}
// ================= CURRENT DATE =================

const currentDate = document.getElementById("currentDate");

const today = new Date();

currentDate.textContent = today.toLocaleDateString("en-IN", {
  day: "numeric",
  month: "long",
  year: "numeric",
});
// ================= DASHBOARD STATISTICS =================

async function loadDashboardStats() {
  try {
    // const response = await fetch("http://127.0.0.1:5000/dashboard-stats");
    const response = await fetch(
      "https://api-medi-scan-ai-analysis.onrender.com/dashboard-stats",
    );

    const data = await response.json();

    // Dashboard cards

    document.getElementById("totalAnalysis").textContent = data.total_analyses;

    document.getElementById("skinAnalysis").textContent = data.skin_analyses;

    document.getElementById("nailAnalysis").textContent = data.nail_analyses;

    document.getElementById("todayAnalysis").textContent = data.today_analyses;

    // Recent analysis table

    const table = document.getElementById("historyTable");

    table.innerHTML = "";

    data.history
      .slice()
      .reverse()
      .forEach((item) => {
        table.innerHTML += `
      <tr>

        <td>${item.date}</td>

        <td>
          <span class="badge ${item.type.toLowerCase()}">
            ${item.type}
          </span>
        </td>

        <td>${item.disease}</td>

        <td class="percentage">
          ${item.probability}%
        </td>

        <td class="percentage">
          ${item.confidence}%
        </td>

        <td>
          <span class="badge ${item.severity.toLowerCase()}">
            ${item.severity}
          </span>
        </td>

      </tr>
    `;
      });
  } catch (error) {
    console.error("Error loading dashboard statistics:", error);
  }
}
// ================= START =================

loadDashboardStats();
