import ExcelJS from "exceljs";
import { prisma } from "@/lib/db";

// ─────────────────────── style tokens ─────────────────────────
const INK = "FF0F1411";
const CREAM = "FFEFE9DD";
const CREAM_PAPER = "FFF6F1E7";
const EMERALD_LIGHT = "FFD1FAE5";
const GOLD_LIGHT = "FFFCEEC8";
const RED = "FFDC5A3E";
const RED_LIGHT = "FFFDE1D9";

const headerStyle: Partial<ExcelJS.Style> = {
  font: { bold: true, color: { argb: CREAM }, size: 11, name: "Inter" },
  fill: { type: "pattern", pattern: "solid", fgColor: { argb: INK } },
  alignment: { vertical: "middle", horizontal: "left" },
  border: {
    bottom: { style: "thin", color: { argb: INK } },
  },
};

function applyHeader(row: ExcelJS.Row) {
  row.eachCell((cell) => {
    cell.style = { ...headerStyle };
  });
  row.height = 22;
}

function riskConditionalFormat(ws: ExcelJS.Worksheet, columnLetter: string, fromRow: number, toRow: number) {
  ws.addConditionalFormatting({
    ref: `${columnLetter}${fromRow}:${columnLetter}${toRow}`,
    rules: [
      {
        type: "containsText",
        operator: "containsText",
        text: "High",
        priority: 1,
        style: {
          fill: { type: "pattern", pattern: "solid", bgColor: { argb: RED_LIGHT }, fgColor: { argb: RED_LIGHT } },
          font: { color: { argb: RED }, bold: true },
        },
      },
      {
        type: "containsText",
        operator: "containsText",
        text: "Medium",
        priority: 2,
        style: {
          fill: { type: "pattern", pattern: "solid", bgColor: { argb: GOLD_LIGHT }, fgColor: { argb: GOLD_LIGHT } },
          font: { color: { argb: "FF78350F" }, bold: true },
        },
      },
      {
        type: "containsText",
        operator: "containsText",
        text: "Low",
        priority: 3,
        style: {
          fill: { type: "pattern", pattern: "solid", bgColor: { argb: EMERALD_LIGHT }, fgColor: { argb: EMERALD_LIGHT } },
          font: { color: { argb: "FF065F46" }, bold: true },
        },
      },
    ],
  });
}

function percentConditionalFormat(
  ws: ExcelJS.Worksheet,
  columnLetter: string,
  fromRow: number,
  toRow: number,
  redBelow = 90
) {
  ws.addConditionalFormatting({
    ref: `${columnLetter}${fromRow}:${columnLetter}${toRow}`,
    rules: [
      {
        type: "cellIs",
        operator: "lessThan",
        formulae: [String(redBelow)],
        priority: 1,
        style: {
          font: { color: { argb: RED }, bold: true },
        },
      },
      {
        type: "cellIs",
        operator: "greaterThan",
        formulae: ["94.99"],
        priority: 2,
        style: {
          font: { color: { argb: "FF065F46" }, bold: true },
        },
      },
    ],
  });
}

// ─────────────────────── workbook builder ─────────────────────
export async function buildHRWorkbook(): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  wb.creator = "Meridian HR Portal";
  wb.created = new Date();
  wb.properties.date1904 = false;

  // Fetch everything from the DB
  const [
    employees,
    finance,
    productivity,
    payroll,
    leaves,
    attrition,
    goals,
    programs,
    enrollments,
    risks,
    positions,
    candidates,
    compliance,
    offboarded,
  ] = await Promise.all([
    prisma.employee.findMany({ orderBy: [{ geo: "asc" }, { id: "asc" }] }),
    prisma.finance.findMany({ include: { employee: true } }),
    prisma.productivity.findMany({ include: { employee: true } }),
    prisma.payroll.findMany({ include: { employee: true } }),
    prisma.leave.findMany({ include: { employee: true } }),
    prisma.attritionRisk.findMany({ include: { employee: true }, orderBy: { totalScore: "desc" } }),
    prisma.goal.findMany({ include: { employee: true } }),
    prisma.trainingProgram.findMany(),
    prisma.trainingEnrollment.findMany({ include: { employee: true, program: true } }),
    prisma.risk.findMany({ include: { employee: true } }),
    prisma.openPosition.findMany(),
    prisma.candidate.findMany({ include: { position: true } }),
    prisma.compliance.findMany(),
    prisma.offboarded.findMany(),
  ]);

  const indiaEmps = employees.filter((e) => e.geo === "India");
  const usEmps = employees.filter((e) => e.geo === "US");
  const totalActive = employees.filter((e) => /Active|Confirmed/.test(e.status)).length;
  const totalIntern = employees.filter((e) => /Intern/i.test(e.status) || /Intern/i.test(e.desig)).length;
  const totalConfirmed = employees.filter((e) => e.status === "Confirmed").length;
  const totalProbation = employees.filter((e) => /Probation/i.test(e.status)).length;
  const internAlerts = employees.filter((e) => {
    if (!e.internEnd) return false;
    const days = Math.floor((new Date(e.internEnd).getTime() - Date.now()) / 86400000);
    return days >= 0 && days <= 45;
  }).length;

  const highRisk = attrition.filter((a) => a.riskLevel === "High").length;
  const medRisk = attrition.filter((a) => a.riskLevel === "Medium").length;
  const lowRisk = attrition.filter((a) => a.riskLevel === "Low").length;

  const totalEverEmployed = employees.length + offboarded.length;
  const attritionRate = totalEverEmployed > 0 ? (offboarded.length / totalEverEmployed) * 100 : 0;

  // ────────────────────── 1. DASHBOARD ─────────────────────────
  const dash = wb.addWorksheet("Dashboard", { views: [{ showGridLines: false }] });
  dash.columns = [
    { width: 28 }, { width: 18 }, { width: 4 }, { width: 28 }, { width: 18 },
  ];

  dash.mergeCells("A1:E1");
  dash.getCell("A1").value = "Meridian HR — Workforce Intelligence Dashboard";
  dash.getCell("A1").font = { size: 22, bold: true, color: { argb: INK }, name: "Fraunces" };
  dash.getCell("A1").alignment = { vertical: "middle" };
  dash.getRow(1).height = 36;

  dash.mergeCells("A2:E2");
  dash.getCell("A2").value = `Report generated ${new Date().toLocaleDateString("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  })} · ${employees.length} employees on roster · ${offboarded.length} historical exits`;
  dash.getCell("A2").font = { size: 10, italic: true, color: { argb: "FF6B6B6B" } };

  // KPI grid
  const kpiStartRow = 4;
  const kpis: [string, number | string, string][] = [
    ["ACTIVE", totalActive, "Confirmed + active"],
    ["CONFIRMED", totalConfirmed, "Past probation"],
    ["INTERNS", totalIntern, "Currently enrolled"],
    ["INTERN ALERTS", internAlerts, "LWD ≤ 45 days"],
    ["PROBATION", totalProbation, "In probation period"],
    ["ATTRITION (TOTAL)", offboarded.length, "All-time exits"],
    ["ATTRITION RATE", `${attritionRate.toFixed(1)}%`, "Offboarded / total ever"],
    ["HIGH-RISK EMPLOYEES", highRisk, "Predictive model"],
    ["MED-RISK EMPLOYEES", medRisk, "Predictive model"],
    ["LOW-RISK EMPLOYEES", lowRisk, "Predictive model"],
  ];

  kpis.forEach((kpi, idx) => {
    const colIdx = idx % 2 === 0 ? 1 : 4;
    const rowIdx = kpiStartRow + Math.floor(idx / 2) * 3;

    // Label cell
    const labelCell = dash.getCell(rowIdx, colIdx);
    labelCell.value = kpi[0];
    labelCell.font = { size: 9, bold: true, color: { argb: "FF6B6B6B" } };
    dash.mergeCells(rowIdx, colIdx, rowIdx, colIdx + 1);

    // Value cell
    const valueCell = dash.getCell(rowIdx + 1, colIdx);
    valueCell.value = kpi[1];
    valueCell.font = { size: 32, bold: true, color: { argb: INK }, name: "Inter" };

    // Hint
    const hintCell = dash.getCell(rowIdx + 1, colIdx + 1);
    hintCell.value = kpi[2];
    hintCell.font = { size: 9, italic: true, color: { argb: "FF888888" } };
    hintCell.alignment = { vertical: "bottom" };

    dash.getRow(rowIdx + 1).height = 38;

    // Fill background
    for (let c = colIdx; c <= colIdx + 1; c++) {
      for (let r = rowIdx; r <= rowIdx + 1; r++) {
        dash.getCell(r, c).fill = {
          type: "pattern",
          pattern: "solid",
          fgColor: { argb: CREAM_PAPER },
        };
      }
    }
  });

  // Department headcount table on dashboard
  const deptStart = kpiStartRow + Math.ceil(kpis.length / 2) * 3 + 2;
  dash.mergeCells(deptStart, 1, deptStart, 5);
  dash.getCell(deptStart, 1).value = "Department headcount";
  dash.getCell(deptStart, 1).font = { size: 16, bold: true, color: { argb: INK }, name: "Fraunces" };

  const deptHead = dash.getRow(deptStart + 1);
  deptHead.values = ["Department", "India", "US", "Total", ""];
  applyHeader(deptHead);

  const deptMap = new Map<string, { india: number; us: number }>();
  for (const e of employees) {
    const row = deptMap.get(e.dept) ?? { india: 0, us: 0 };
    if (e.geo === "India") row.india++; else row.us++;
    deptMap.set(e.dept, row);
  }
  const depts = Array.from(deptMap.entries()).sort((a, b) => (b[1].india + b[1].us) - (a[1].india + a[1].us));
  depts.forEach(([name, counts], i) => {
    const r = deptStart + 2 + i;
    dash.getCell(r, 1).value = name;
    dash.getCell(r, 2).value = counts.india;
    dash.getCell(r, 3).value = counts.us;
    dash.getCell(r, 4).value = { formula: `B${r}+C${r}` };
    dash.getCell(r, 4).font = { bold: true };
  });
  const totalRow = deptStart + 2 + depts.length;
  dash.getCell(totalRow, 1).value = "TOTAL";
  dash.getCell(totalRow, 1).font = { bold: true };
  dash.getCell(totalRow, 2).value = { formula: `SUM(B${deptStart + 2}:B${totalRow - 1})` };
  dash.getCell(totalRow, 3).value = { formula: `SUM(C${deptStart + 2}:C${totalRow - 1})` };
  dash.getCell(totalRow, 4).value = { formula: `SUM(D${deptStart + 2}:D${totalRow - 1})` };
  dash.getRow(totalRow).font = { bold: true };

  // Top attrition risks
  const topStart = totalRow + 3;
  dash.mergeCells(topStart, 1, topStart, 5);
  dash.getCell(topStart, 1).value = "Top attrition risks";
  dash.getCell(topStart, 1).font = { size: 16, bold: true, color: { argb: INK }, name: "Fraunces" };

  const topHead = dash.getRow(topStart + 1);
  topHead.values = ["Employee", "Department", "Geo", "Score", "Risk level"];
  applyHeader(topHead);

  const top10 = attrition.slice(0, 10);
  top10.forEach((r, i) => {
    const row = dash.getRow(topStart + 2 + i);
    row.values = [r.employee.name, r.employee.dept, r.employee.geo, Number(r.totalScore.toFixed(2)), r.riskLevel];
  });
  riskConditionalFormat(dash, "E", topStart + 2, topStart + 1 + top10.length);

  // ────────────────────── 2. INDIA EMPLOYEES ───────────────────
  const indiaWs = wb.addWorksheet("India Employees");
  indiaWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Department", key: "dept", width: 18 },
    { header: "Designation", key: "desig", width: 24 },
    { header: "Reporting Manager", key: "manager", width: 24 },
    { header: "Skill / Tech Stack", key: "skill", width: 26 },
    { header: "DOJ", key: "doj", width: 12 },
    { header: "Employment Status", key: "status", width: 16 },
    { header: "LWD", key: "lwd", width: 12 },
    { header: "Intern End Date", key: "internEnd", width: 14 },
  ];
  applyHeader(indiaWs.getRow(1));
  indiaEmps.forEach((e) =>
    indiaWs.addRow({
      id: e.id, name: e.name, dept: e.dept, desig: e.desig,
      manager: e.manager ?? "", skill: e.skill ?? "",
      doj: e.doj, status: e.status, lwd: e.lwd ?? "", internEnd: e.internEnd ?? "",
    })
  );
  indiaWs.views = [{ state: "frozen", ySplit: 1 }];
  indiaWs.autoFilter = { from: "A1", to: `J${indiaEmps.length + 1}` };

  // ────────────────────── 3. US EMPLOYEES ──────────────────────
  const usWs = wb.addWorksheet("US Employees");
  usWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Department", key: "dept", width: 18 },
    { header: "Designation", key: "desig", width: 24 },
    { header: "Reporting Manager", key: "manager", width: 24 },
    { header: "Skill / Tech Stack", key: "skill", width: 26 },
    { header: "DOJ", key: "doj", width: 12 },
    { header: "Employment Status", key: "status", width: 16 },
    { header: "Current Allocation %", key: "allocation", width: 18 },
    { header: "LWD", key: "lwd", width: 12 },
    { header: "Intern End Date", key: "internEnd", width: 14 },
  ];
  applyHeader(usWs.getRow(1));
  usEmps.forEach((e) =>
    usWs.addRow({
      id: e.id, name: e.name, dept: e.dept, desig: e.desig,
      manager: e.manager ?? "", skill: e.skill ?? "",
      doj: e.doj, status: e.status, allocation: e.allocation ?? "",
      lwd: e.lwd ?? "", internEnd: e.internEnd ?? "",
    })
  );
  usWs.views = [{ state: "frozen", ySplit: 1 }];
  usWs.autoFilter = { from: "A1", to: `K${usEmps.length + 1}` };

  // ────────────────────── 4. FINANCE ───────────────────────────
  const finWs = wb.addWorksheet("Finance");
  finWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Designation", key: "desig", width: 24 },
    { header: "Annual (INR)", key: "annualInr", width: 16, style: { numFmt: "#,##0" } },
    { header: "Monthly (INR)", key: "monthlyInr", width: 16, style: { numFmt: "#,##0" } },
    { header: "Annual (USD)", key: "annualUsd", width: 16, style: { numFmt: "#,##0" } },
    { header: "Monthly (USD)", key: "monthlyUsd", width: 16, style: { numFmt: "#,##0" } },
  ];
  applyHeader(finWs.getRow(1));
  finance.forEach((f) =>
    finWs.addRow({
      id: f.employeeId, name: f.employee.name, geo: f.employee.geo,
      dept: f.employee.dept, desig: f.employee.desig,
      annualInr: f.annualInr, monthlyInr: f.monthlyInr,
      annualUsd: f.annualUsd, monthlyUsd: f.monthlyUsd,
    })
  );
  finWs.views = [{ state: "frozen", ySplit: 1 }];
  finWs.autoFilter = { from: "A1", to: `I${finance.length + 1}` };

  // ────────────────────── 5. PRODUCTIVITY ──────────────────────
  const prodWs = wb.addWorksheet("Productivity");
  prodWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Designation", key: "desig", width: 24 },
    { header: "Score", key: "score", width: 10 },
    { header: "Tasks Completed", key: "tasks", width: 16 },
    { header: "On-Time %", key: "ontime", width: 12 },
  ];
  applyHeader(prodWs.getRow(1));
  productivity.forEach((p) =>
    prodWs.addRow({
      id: p.employeeId, name: p.employee.name, geo: p.employee.geo,
      dept: p.employee.dept, desig: p.employee.desig,
      score: Number(p.score.toFixed(2)),
      tasks: p.tasksCompleted,
      ontime: p.onTimePct,
    })
  );
  prodWs.views = [{ state: "frozen", ySplit: 1 }];
  prodWs.autoFilter = { from: "A1", to: `H${productivity.length + 1}` };
  percentConditionalFormat(prodWs, "H", 2, productivity.length + 1, 80);

  // ────────────────────── 6. PAYROLL ───────────────────────────
  const payWs = wb.addWorksheet("Payroll");
  payWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "CTC", key: "ctc", width: 14, style: { numFmt: "#,##0" } },
    { header: "Basic", key: "basic", width: 12, style: { numFmt: "#,##0" } },
    { header: "HRA", key: "hra", width: 12, style: { numFmt: "#,##0" } },
    { header: "Special", key: "special", width: 12, style: { numFmt: "#,##0" } },
    { header: "Gross", key: "gross", width: 12, style: { numFmt: "#,##0" } },
    { header: "PF (Emp)", key: "pfEmp", width: 12, style: { numFmt: "#,##0" } },
    { header: "ESI", key: "esi", width: 10, style: { numFmt: "#,##0" } },
    { header: "PT", key: "pt", width: 10, style: { numFmt: "#,##0" } },
    { header: "TDS", key: "tds", width: 12, style: { numFmt: "#,##0" } },
    { header: "Net Pay", key: "net", width: 14, style: { numFmt: "#,##0" } },
    { header: "Currency", key: "currency", width: 10 },
  ];
  applyHeader(payWs.getRow(1));
  payroll.forEach((p) =>
    payWs.addRow({
      id: p.employeeId, name: p.employee.name, geo: p.employee.geo,
      dept: p.employee.dept,
      ctc: p.ctc, basic: p.basic, hra: p.hra, special: p.special,
      gross: p.gross, pfEmp: p.pfEmp, esi: p.esi, pt: p.pt, tds: p.tds,
      net: p.net, currency: p.currency,
    })
  );
  payWs.views = [{ state: "frozen", ySplit: 1 }];
  payWs.autoFilter = { from: "A1", to: `O${payroll.length + 1}` };

  // ────────────────────── 7. LEAVE & ATTENDANCE ────────────────
  const leaveWs = wb.addWorksheet("Leave & Attendance");
  leaveWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Department", key: "dept", width: 16 },
    { header: "CL Entitled", key: "ce", width: 12 },
    { header: "CL Used", key: "cu", width: 10 },
    { header: "CL Balance", key: "cb", width: 12 },
    { header: "SL Entitled", key: "se", width: 12 },
    { header: "SL Used", key: "su", width: 10 },
    { header: "SL Balance", key: "sb", width: 12 },
    { header: "EL Entitled", key: "ee", width: 12 },
    { header: "EL Used", key: "eu", width: 10 },
    { header: "EL Balance", key: "eb", width: 12 },
    { header: "Attendance %", key: "att", width: 14 },
  ];
  applyHeader(leaveWs.getRow(1));
  leaves.forEach((l) =>
    leaveWs.addRow({
      id: l.employeeId, name: l.employee.name, dept: l.employee.dept,
      ce: l.clEntitled, cu: l.clUsed, cb: l.clBalance,
      se: l.slEntitled, su: l.slUsed, sb: l.slBalance,
      ee: l.elEntitled, eu: l.elUsed, eb: l.elBalance,
      att: l.attendancePct,
    })
  );
  leaveWs.views = [{ state: "frozen", ySplit: 1 }];
  leaveWs.autoFilter = { from: "A1", to: `M${leaves.length + 1}` };
  percentConditionalFormat(leaveWs, "M", 2, leaves.length + 1, 90);

  // ────────────────────── 8. ATTRITION RISK ────────────────────
  const riskWs = wb.addWorksheet("Attrition Risk");
  riskWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Designation", key: "desig", width: 24 },
    { header: "Tenure (days)", key: "tenure", width: 14 },
    { header: "Tenure Score", key: "ts", width: 12 },
    { header: "Productivity Score", key: "ps", width: 16 },
    { header: "Comp Score", key: "cs", width: 12 },
    { header: "Other Score", key: "os", width: 12 },
    { header: "Total Score", key: "total", width: 12 },
    { header: "Risk Level", key: "level", width: 12 },
    { header: "Top Reason", key: "reason", width: 28 },
  ];
  applyHeader(riskWs.getRow(1));
  attrition.forEach((a) =>
    riskWs.addRow({
      id: a.employeeId, name: a.employee.name, geo: a.employee.geo,
      dept: a.employee.dept, desig: a.employee.desig,
      tenure: a.tenureDays,
      ts: Number(a.tenureScore.toFixed(2)),
      ps: Number(a.prodScore.toFixed(2)),
      cs: Number(a.compScore.toFixed(2)),
      os: Number(a.otherScore.toFixed(2)),
      total: Number(a.totalScore.toFixed(2)),
      level: a.riskLevel,
      reason: a.topReason,
    })
  );
  riskWs.views = [{ state: "frozen", ySplit: 1 }];
  riskWs.autoFilter = { from: "A1", to: `M${attrition.length + 1}` };
  riskConditionalFormat(riskWs, "L", 2, attrition.length + 1);

  // ────────────────────── 9. RISK REPORT ───────────────────────
  const riskRptWs = wb.addWorksheet("Risk Report");
  riskRptWs.columns = [
    { header: "Risk ID", key: "id", width: 12 },
    { header: "Employee ID", key: "eid", width: 14 },
    { header: "Employee Name", key: "name", width: 24 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Category", key: "cat", width: 18 },
    { header: "Level", key: "level", width: 10 },
    { header: "Raised On", key: "raised", width: 14 },
    { header: "Status", key: "status", width: 14 },
    { header: "Owner", key: "owner", width: 16 },
    { header: "Notes", key: "notes", width: 40 },
  ];
  applyHeader(riskRptWs.getRow(1));
  risks.forEach((r) =>
    riskRptWs.addRow({
      id: r.id, eid: r.employeeId, name: r.employee.name,
      geo: r.employee.geo, dept: r.employee.dept,
      cat: r.category, level: r.level, raised: r.raisedOn,
      status: r.status, owner: r.owner ?? "", notes: r.notes ?? "",
    })
  );
  riskRptWs.views = [{ state: "frozen", ySplit: 1 }];
  riskConditionalFormat(riskRptWs, "G", 2, risks.length + 1);

  // ────────────────────── 10. OFFBOARDED ───────────────────────
  const offWs = wb.addWorksheet("Offboarded Resources");
  offWs.columns = [
    { header: "Employee ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 24 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Designation", key: "desig", width: 24 },
    { header: "DOJ", key: "doj", width: 12 },
    { header: "LWD", key: "lwd", width: 12 },
    { header: "Quarter", key: "qtr", width: 10 },
    { header: "Reason", key: "reason", width: 22 },
    { header: "Tenure (yrs)", key: "tenure", width: 12 },
  ];
  applyHeader(offWs.getRow(1));
  offboarded.forEach((o) =>
    offWs.addRow({
      id: o.id, name: o.name, geo: o.geo, dept: o.dept, desig: o.desig,
      doj: o.doj, lwd: o.lwd, qtr: o.quarter, reason: o.reason, tenure: o.tenureYears,
    })
  );
  offWs.views = [{ state: "frozen", ySplit: 1 }];

  // ────────────────────── 11. GOALS ────────────────────────────
  const goalWs = wb.addWorksheet("Goals");
  goalWs.columns = [
    { header: "Goal ID", key: "id", width: 12 },
    { header: "Employee ID", key: "eid", width: 14 },
    { header: "Employee Name", key: "name", width: 22 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Title", key: "title", width: 36 },
    { header: "Target", key: "target", width: 12 },
    { header: "Actual", key: "actual", width: 12 },
    { header: "Unit", key: "unit", width: 12 },
    { header: "Weight", key: "weight", width: 10 },
    { header: "Achievement %", key: "ach", width: 14 },
    { header: "Rating", key: "rating", width: 10 },
    { header: "Status", key: "status", width: 14 },
  ];
  applyHeader(goalWs.getRow(1));
  goals.forEach((g) =>
    goalWs.addRow({
      id: g.id, eid: g.employeeId, name: g.employee.name,
      geo: g.employee.geo, dept: g.employee.dept,
      title: g.title, target: g.target, actual: g.actual,
      unit: g.unit ?? "", weight: g.weight,
      ach: Number(g.achievementPct.toFixed(1)),
      rating: g.rating ?? "", status: g.status,
    })
  );
  goalWs.views = [{ state: "frozen", ySplit: 1 }];

  // ────────────────────── 12. TRAINING ─────────────────────────
  const tpWs = wb.addWorksheet("Training Programs");
  tpWs.columns = [
    { header: "Program ID", key: "id", width: 12 },
    { header: "Title", key: "title", width: 36 },
    { header: "Category", key: "cat", width: 16 },
    { header: "Duration (hrs)", key: "hrs", width: 14 },
    { header: "Mandatory", key: "mand", width: 12 },
    { header: "Target", key: "target", width: 22 },
  ];
  applyHeader(tpWs.getRow(1));
  programs.forEach((p) =>
    tpWs.addRow({
      id: p.id, title: p.title, cat: p.category,
      hrs: p.durationHrs, mand: p.mandatory ? "Yes" : "No", target: p.target ?? "",
    })
  );
  tpWs.views = [{ state: "frozen", ySplit: 1 }];

  const teWs = wb.addWorksheet("Training Enrollments");
  teWs.columns = [
    { header: "Enrollment ID", key: "id", width: 14 },
    { header: "Employee ID", key: "eid", width: 14 },
    { header: "Employee Name", key: "name", width: 22 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Program ID", key: "tid", width: 12 },
    { header: "Program Title", key: "ttitle", width: 30 },
    { header: "Category", key: "cat", width: 16 },
    { header: "Mandatory", key: "mand", width: 12 },
    { header: "Completion %", key: "pct", width: 14 },
    { header: "Status", key: "status", width: 14 },
  ];
  applyHeader(teWs.getRow(1));
  enrollments.forEach((e) =>
    teWs.addRow({
      id: e.id, eid: e.employeeId, name: e.employee.name,
      geo: e.employee.geo, dept: e.employee.dept,
      tid: e.programId, ttitle: e.program.title, cat: e.program.category,
      mand: e.program.mandatory ? "Yes" : "No",
      pct: e.completionPct, status: e.status,
    })
  );
  teWs.views = [{ state: "frozen", ySplit: 1 }];
  teWs.autoFilter = { from: "A1", to: `K${enrollments.length + 1}` };

  // ────────────────────── 13. RECRUITMENT ──────────────────────
  const posWs = wb.addWorksheet("Open Positions");
  posWs.columns = [
    { header: "Position ID", key: "id", width: 14 },
    { header: "Title", key: "title", width: 30 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Openings", key: "openings", width: 10 },
    { header: "Priority", key: "priority", width: 12 },
    { header: "Days Open", key: "days", width: 12 },
  ];
  applyHeader(posWs.getRow(1));
  positions.forEach((p) =>
    posWs.addRow({
      id: p.id, title: p.title, dept: p.dept, geo: p.geo,
      openings: p.openings, priority: p.priority, days: p.daysOpen,
    })
  );
  posWs.views = [{ state: "frozen", ySplit: 1 }];

  const candWs = wb.addWorksheet("Candidates");
  candWs.columns = [
    { header: "Candidate ID", key: "id", width: 14 },
    { header: "Name", key: "name", width: 22 },
    { header: "Position ID", key: "pid", width: 12 },
    { header: "Position Title", key: "ptitle", width: 28 },
    { header: "Department", key: "dept", width: 16 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Stage", key: "stage", width: 16 },
    { header: "Days in Stage", key: "days", width: 14 },
    { header: "Source", key: "source", width: 14 },
    { header: "Rating", key: "rating", width: 10 },
  ];
  applyHeader(candWs.getRow(1));
  candidates.forEach((c) =>
    candWs.addRow({
      id: c.id, name: c.name, pid: c.positionId, ptitle: c.position.title,
      dept: c.position.dept, geo: c.position.geo,
      stage: c.stage, days: c.daysInStage, source: c.source,
      rating: c.rating ?? "",
    })
  );
  candWs.views = [{ state: "frozen", ySplit: 1 }];

  // ────────────────────── 14. COMPLIANCE ───────────────────────
  const compWs = wb.addWorksheet("Compliance");
  compWs.columns = [
    { header: "ID", key: "id", width: 10 },
    { header: "Title", key: "title", width: 36 },
    { header: "Category", key: "cat", width: 16 },
    { header: "Geo", key: "geo", width: 8 },
    { header: "Due Date", key: "due", width: 14 },
    { header: "Frequency", key: "freq", width: 12 },
    { header: "Authority", key: "auth", width: 18 },
    { header: "Status", key: "status", width: 14 },
  ];
  applyHeader(compWs.getRow(1));
  compliance.forEach((c) =>
    compWs.addRow({
      id: c.id, title: c.title, cat: c.category, geo: c.geo,
      due: c.dueDate, freq: c.frequency, auth: c.authority, status: c.status,
    })
  );
  compWs.views = [{ state: "frozen", ySplit: 1 }];

  const arrayBuffer = await wb.xlsx.writeBuffer();
  return Buffer.from(arrayBuffer);
}

// ─────────────────── CSV helper ───────────────────
export function toCSV(rows: Record<string, any>[], columns: { key: string; header: string }[]): string {
  const escape = (val: any) => {
    if (val == null) return "";
    const s = String(val);
    if (s.includes(",") || s.includes('"') || s.includes("\n")) {
      return `"${s.replace(/"/g, '""')}"`;
    }
    return s;
  };

  const header = columns.map((c) => escape(c.header)).join(",");
  const body = rows
    .map((row) => columns.map((c) => escape(row[c.key])).join(","))
    .join("\n");
  return header + "\n" + body;
}
