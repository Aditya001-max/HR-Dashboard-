import { NextRequest, NextResponse } from "next/server";
import ExcelJS from "exceljs";
import { prisma } from "@/lib/db";

export const dynamic = "force-dynamic";
export const maxDuration = 60;

type Row = { [key: string]: any };

function asStr(v: any): string | null {
  if (v == null || v === "") return null;
  if (typeof v === "object" && "text" in v) return String((v as any).text);
  if (typeof v === "object" && "result" in v) return String((v as any).result);
  return String(v);
}

function asNum(v: any): number | null {
  if (v == null || v === "") return null;
  if (typeof v === "object" && "result" in v) return Number((v as any).result);
  const n = Number(v);
  return isNaN(n) ? null : n;
}

function asBool(v: any): boolean {
  const s = asStr(v)?.toLowerCase() ?? "";
  return s === "yes" || s === "true" || s === "1";
}

// Read sheet into an array of objects keyed by header text.
function sheetToObjects(ws: ExcelJS.Worksheet): Row[] {
  const headerRow = ws.getRow(1);
  const headers: string[] = [];
  headerRow.eachCell((cell, col) => {
    headers[col] = String(cell.value ?? "").trim();
  });
  const rows: Row[] = [];
  ws.eachRow((row, rowIdx) => {
    if (rowIdx === 1) return;
    const obj: Row = {};
    let hasData = false;
    row.eachCell((cell, col) => {
      const key = headers[col];
      if (!key) return;
      obj[key] = cell.value;
      if (cell.value != null && cell.value !== "") hasData = true;
    });
    if (hasData) rows.push(obj);
  });
  return rows;
}

function findColumn(row: Row, candidates: string[]): any {
  for (const c of candidates) {
    if (c in row) return row[c];
    const found = Object.keys(row).find((k) => k.toLowerCase() === c.toLowerCase());
    if (found) return row[found];
  }
  return undefined;
}

export async function POST(req: NextRequest) {
  let formData: FormData;
  try {
    formData = await req.formData();
  } catch {
    return NextResponse.json({ error: "Failed to parse upload" }, { status: 400 });
  }

  const file = formData.get("file") as File | null;
  if (!file) {
    return NextResponse.json({ error: "No file uploaded" }, { status: 400 });
  }
  if (!/\.(xlsx|xlsm)$/i.test(file.name)) {
    return NextResponse.json(
      { error: "Only .xlsx files are supported. Convert .csv/.xls to .xlsx first." },
      { status: 400 }
    );
  }

  const buf = Buffer.from(await file.arrayBuffer());
  const wb = new ExcelJS.Workbook();
  try {
    await wb.xlsx.load(buf as any);
  } catch (e: any) {
    return NextResponse.json({ error: `Could not parse workbook: ${e.message}` }, { status: 400 });
  }

  // ─────── Parse all known sheets ───────
  const sheetMap: Record<string, ExcelJS.Worksheet | undefined> = {};
  wb.eachSheet((ws) => {
    sheetMap[ws.name.toLowerCase()] = ws;
  });

  function getSheet(...names: string[]): ExcelJS.Worksheet | undefined {
    for (const n of names) {
      const ws = sheetMap[n.toLowerCase()];
      if (ws) return ws;
    }
    return undefined;
  }

  const indiaWs = getSheet("India Employees", "India");
  const usWs = getSheet("US Employees", "US");
  const financeWs = getSheet("Finance", "Compensation");
  const productivityWs = getSheet("Productivity");
  const payrollWs = getSheet("Payroll");
  const leaveWs = getSheet("Leave & Attendance", "Leave", "Attendance");
  const attritionWs = getSheet("Attrition Risk", "Risk Score");
  const offboardedWs = getSheet("Offboarded Resources", "Offboarded");
  const complianceWs = getSheet("Compliance");
  const goalsWs = getSheet("Goals", "Goal");
  const trainingProgramsWs = getSheet("Training Programs", "Training Program");
  const trainingEnrollmentsWs = getSheet("Training Enrollments", "Enrollments");
  const risksWs = getSheet("Risk Report", "Risks");
  const openPositionsWs = getSheet("Open Positions", "Positions");
  const candidatesWs = getSheet("Candidates");

  if (!indiaWs && !usWs) {
    return NextResponse.json(
      {
        error:
          "Workbook is missing both 'India Employees' and 'US Employees' sheets. At least one is required.",
        availableSheets: Object.keys(sheetMap),
      },
      { status: 400 }
    );
  }

  // ─────── Build employee records ───────
  type EmpInput = {
    id: string;
    name: string;
    geo: string;
    dept: string;
    desig: string;
    manager: string | null;
    skill: string | null;
    doj: string;
    status: string;
    lwd: string | null;
    internEnd: string | null;
    allocation: string | null;
  };

  function parseEmployees(ws: ExcelJS.Worksheet | undefined, geo: string): EmpInput[] {
    if (!ws) return [];
    const rows = sheetToObjects(ws);
    return rows
      .map((r) => {
        const id = asStr(findColumn(r, ["Employee ID", "ID", "Emp ID"]));
        const name = asStr(findColumn(r, ["Name", "Employee Name", "Full Name"]));
        if (!id || !name) return null;
        return {
          id,
          name,
          geo,
          dept: asStr(findColumn(r, ["Department", "Dept"])) ?? "Unassigned",
          desig: asStr(findColumn(r, ["Designation", "Role", "Title"])) ?? "—",
          manager: asStr(findColumn(r, ["Reporting Manager", "Manager"])),
          skill: asStr(findColumn(r, ["Skill / Tech Stack", "Skill", "Tech Stack"])),
          doj: asStr(findColumn(r, ["DOJ", "Date of Joining", "Joining Date"])) ?? "",
          status: asStr(findColumn(r, ["Employment Status", "Status"])) ?? "Active",
          lwd: asStr(findColumn(r, ["LWD", "Last Working Day"])),
          internEnd: asStr(findColumn(r, ["Intern End Date", "Intern End"])),
          allocation: asStr(findColumn(r, ["Current Allocation %", "Allocation"])),
        } as EmpInput;
      })
      .filter((x): x is EmpInput => x !== null);
  }

  const indiaEmps = parseEmployees(indiaWs, "India");
  const usEmps = parseEmployees(usWs, "US");
  const allEmps = [...indiaEmps, ...usEmps];

  if (allEmps.length === 0) {
    return NextResponse.json(
      { error: "No employee rows found. Check that columns 'Employee ID' and 'Name' exist." },
      { status: 400 }
    );
  }

  const empIds = new Set(allEmps.map((e) => e.id));

  // Helper: parse rows that reference an Employee ID
  function parseLinked<T>(
    ws: ExcelJS.Worksheet | undefined,
    map: (r: Row) => T | null
  ): T[] {
    if (!ws) return [];
    return sheetToObjects(ws)
      .map(map)
      .filter((x): x is T => x !== null);
  }

  const financeRows = parseLinked(financeWs, (r) => {
    const id = asStr(findColumn(r, ["Employee ID", "ID"]));
    if (!id || !empIds.has(id)) return null;
    return {
      employeeId: id,
      annualInr: asNum(findColumn(r, ["Annual (INR)", "Annual INR"])),
      monthlyInr: asNum(findColumn(r, ["Monthly (INR)", "Monthly INR"])),
      annualUsd: asNum(findColumn(r, ["Annual (USD)", "Annual USD"])),
      monthlyUsd: asNum(findColumn(r, ["Monthly (USD)", "Monthly USD"])),
    };
  });

  const productivityRows = parseLinked(productivityWs, (r) => {
    const id = asStr(findColumn(r, ["Employee ID", "ID"]));
    if (!id || !empIds.has(id)) return null;
    return {
      employeeId: id,
      score: asNum(findColumn(r, ["Score", "Productivity Score"])) ?? 0,
      tasksCompleted: Math.round(asNum(findColumn(r, ["Tasks Completed", "Tasks"])) ?? 0),
      onTimePct: asNum(findColumn(r, ["On-Time %", "On Time %"])) ?? 0,
    };
  });

  const payrollRows = parseLinked(payrollWs, (r) => {
    const id = asStr(findColumn(r, ["Employee ID", "ID"]));
    if (!id || !empIds.has(id)) return null;
    return {
      employeeId: id,
      ctc: asNum(findColumn(r, ["CTC"])) ?? 0,
      basic: asNum(findColumn(r, ["Basic"])) ?? 0,
      hra: asNum(findColumn(r, ["HRA"])) ?? 0,
      special: asNum(findColumn(r, ["Special"])) ?? 0,
      gross: asNum(findColumn(r, ["Gross"])) ?? 0,
      pfEmp: asNum(findColumn(r, ["PF (Emp)", "PF (Employee)"])) ?? 0,
      pfEmr: asNum(findColumn(r, ["PF (Emr)", "PF (Employer)"])) ?? 0,
      esi: asNum(findColumn(r, ["ESI"])) ?? 0,
      pt: asNum(findColumn(r, ["PT"])) ?? 0,
      tds: asNum(findColumn(r, ["TDS"])) ?? 0,
      net: asNum(findColumn(r, ["Net Pay", "Net"])) ?? 0,
      currency: asStr(findColumn(r, ["Currency"])) ?? "INR",
    };
  });

  const leaveRows = parseLinked(leaveWs, (r) => {
    const id = asStr(findColumn(r, ["Employee ID", "ID"]));
    if (!id || !empIds.has(id)) return null;
    return {
      employeeId: id,
      clEntitled: Math.round(asNum(findColumn(r, ["CL Entitled"])) ?? 0),
      clUsed: Math.round(asNum(findColumn(r, ["CL Used"])) ?? 0),
      clBalance: Math.round(asNum(findColumn(r, ["CL Balance"])) ?? 0),
      slEntitled: Math.round(asNum(findColumn(r, ["SL Entitled"])) ?? 0),
      slUsed: Math.round(asNum(findColumn(r, ["SL Used"])) ?? 0),
      slBalance: Math.round(asNum(findColumn(r, ["SL Balance"])) ?? 0),
      elEntitled: Math.round(asNum(findColumn(r, ["EL Entitled"])) ?? 0),
      elUsed: Math.round(asNum(findColumn(r, ["EL Used"])) ?? 0),
      elBalance: Math.round(asNum(findColumn(r, ["EL Balance"])) ?? 0),
      attendancePct: asNum(findColumn(r, ["Attendance %"])) ?? 0,
    };
  });

  const attritionRows = parseLinked(attritionWs, (r) => {
    const id = asStr(findColumn(r, ["Employee ID", "ID"]));
    if (!id || !empIds.has(id)) return null;
    return {
      employeeId: id,
      tenureDays: Math.round(asNum(findColumn(r, ["Tenure (days)", "Tenure"])) ?? 0),
      tenureScore: asNum(findColumn(r, ["Tenure Score"])) ?? 0,
      prodScore: asNum(findColumn(r, ["Productivity Score"])) ?? 0,
      compScore: asNum(findColumn(r, ["Comp Score"])) ?? 0,
      otherScore: asNum(findColumn(r, ["Other Score"])) ?? 0,
      totalScore: asNum(findColumn(r, ["Total Score"])) ?? 0,
      riskLevel: asStr(findColumn(r, ["Risk Level"])) ?? "Low",
      topReason: asStr(findColumn(r, ["Top Reason", "Reason"])) ?? "—",
    };
  });

  const offboardedRows = parseLinked(offboardedWs, (r) => {
    const id = asStr(findColumn(r, ["Employee ID", "ID"]));
    const name = asStr(findColumn(r, ["Name", "Employee Name"]));
    if (!id || !name) return null;
    return {
      id,
      name,
      geo: asStr(findColumn(r, ["Geo"])) ?? "India",
      dept: asStr(findColumn(r, ["Department", "Dept"])) ?? "—",
      desig: asStr(findColumn(r, ["Designation"])) ?? "—",
      doj: asStr(findColumn(r, ["DOJ"])) ?? "",
      lwd: asStr(findColumn(r, ["LWD"])) ?? "",
      quarter: asStr(findColumn(r, ["Quarter"])) ?? "",
      reason: asStr(findColumn(r, ["Reason"])) ?? "—",
      tenureYears: asNum(findColumn(r, ["Tenure (yrs)", "Tenure Years", "Tenure"])) ?? 0,
    };
  });

  const complianceRows = parseLinked(complianceWs, (r) => {
    const id = asStr(findColumn(r, ["ID", "Compliance ID"]));
    const title = asStr(findColumn(r, ["Title"]));
    if (!id || !title) return null;
    return {
      id,
      title,
      category: asStr(findColumn(r, ["Category"])) ?? "General",
      geo: asStr(findColumn(r, ["Geo"])) ?? "India",
      dueDate: asStr(findColumn(r, ["Due Date"])) ?? "",
      frequency: asStr(findColumn(r, ["Frequency"])) ?? "—",
      authority: asStr(findColumn(r, ["Authority"])) ?? "—",
      status: asStr(findColumn(r, ["Status"])) ?? "Pending",
    };
  });

  const goalsRows = parseLinked(goalsWs, (r) => {
    const id = asStr(findColumn(r, ["Goal ID", "ID"]));
    const empId = asStr(findColumn(r, ["Employee ID"]));
    const title = asStr(findColumn(r, ["Title", "Goal Title"]));
    if (!id || !empId || !empIds.has(empId) || !title) return null;
    return {
      id,
      employeeId: empId,
      title,
      description: asStr(findColumn(r, ["Description"])),
      unit: asStr(findColumn(r, ["Unit"])),
      target: asNum(findColumn(r, ["Target"])) ?? 0,
      actual: asNum(findColumn(r, ["Actual"])) ?? 0,
      weight: asNum(findColumn(r, ["Weight"])) ?? 0,
      achievementPct: asNum(findColumn(r, ["Achievement %", "Achievement"])) ?? 0,
      rating: asNum(findColumn(r, ["Rating"])),
      status: asStr(findColumn(r, ["Status"])) ?? "In Progress",
    };
  });

  const trainingProgramRows = parseLinked(trainingProgramsWs, (r) => {
    const id = asStr(findColumn(r, ["Program ID", "ID", "Train ID"]));
    const title = asStr(findColumn(r, ["Title"]));
    if (!id || !title) return null;
    return {
      id,
      title,
      category: asStr(findColumn(r, ["Category"])) ?? "General",
      durationHrs: Math.round(asNum(findColumn(r, ["Duration (hrs)", "Duration"])) ?? 0),
      mandatory: asBool(findColumn(r, ["Mandatory"])),
      target: asStr(findColumn(r, ["Target"])),
    };
  });
  const programIds = new Set(trainingProgramRows.map((p) => p.id));

  const trainingEnrollmentRows = parseLinked(trainingEnrollmentsWs, (r) => {
    const id = asStr(findColumn(r, ["Enrollment ID", "ID"]));
    const empId = asStr(findColumn(r, ["Employee ID"]));
    const programId = asStr(findColumn(r, ["Program ID", "Train ID"]));
    if (!id || !empId || !programId) return null;
    if (!empIds.has(empId) || !programIds.has(programId)) return null;
    return {
      id,
      employeeId: empId,
      programId,
      completionPct: asNum(findColumn(r, ["Completion %", "Completion"])) ?? 0,
      status: asStr(findColumn(r, ["Status"])) ?? "Not Started",
    };
  });

  const risksRows = parseLinked(risksWs, (r) => {
    const id = asStr(findColumn(r, ["Risk ID", "ID"]));
    const empId = asStr(findColumn(r, ["Employee ID"]));
    if (!id || !empId || !empIds.has(empId)) return null;
    return {
      id,
      employeeId: empId,
      category: asStr(findColumn(r, ["Category"])) ?? "General",
      level: asStr(findColumn(r, ["Level"])) ?? "Low",
      raisedOn: asStr(findColumn(r, ["Raised On"])) ?? "",
      status: asStr(findColumn(r, ["Status"])) ?? "Open",
      owner: asStr(findColumn(r, ["Owner"])),
      notes: asStr(findColumn(r, ["Notes"])),
    };
  });

  const openPositionRows = parseLinked(openPositionsWs, (r) => {
    const id = asStr(findColumn(r, ["Position ID", "ID", "Pos ID"]));
    const title = asStr(findColumn(r, ["Title"]));
    if (!id || !title) return null;
    return {
      id,
      title,
      dept: asStr(findColumn(r, ["Department", "Dept"])) ?? "—",
      geo: asStr(findColumn(r, ["Geo"])) ?? "India",
      openings: Math.round(asNum(findColumn(r, ["Openings"])) ?? 1),
      priority: asStr(findColumn(r, ["Priority"])) ?? "Medium",
      daysOpen: Math.round(asNum(findColumn(r, ["Days Open"])) ?? 0),
    };
  });
  const positionIds = new Set(openPositionRows.map((p) => p.id));

  const candidateRows = parseLinked(candidatesWs, (r) => {
    const id = asStr(findColumn(r, ["Candidate ID", "ID", "Cand ID"]));
    const name = asStr(findColumn(r, ["Name"]));
    const positionId = asStr(findColumn(r, ["Position ID", "Pos ID"]));
    if (!id || !name || !positionId || !positionIds.has(positionId)) return null;
    return {
      id,
      name,
      positionId,
      stage: asStr(findColumn(r, ["Stage"])) ?? "Sourced",
      daysInStage: Math.round(asNum(findColumn(r, ["Days in Stage"])) ?? 0),
      source: asStr(findColumn(r, ["Source"])) ?? "—",
      rating: asNum(findColumn(r, ["Rating"])),
    };
  });

  // ─────── Replace DB inside a transaction ───────
  try {
    await prisma.$transaction(
      async (tx) => {
        // Wipe in FK order
        await tx.candidate.deleteMany();
        await tx.openPosition.deleteMany();
        await tx.trainingEnrollment.deleteMany();
        await tx.trainingProgram.deleteMany();
        await tx.risk.deleteMany();
        await tx.goal.deleteMany();
        await tx.attritionRisk.deleteMany();
        await tx.leave.deleteMany();
        await tx.payroll.deleteMany();
        await tx.productivity.deleteMany();
        await tx.finance.deleteMany();
        await tx.employee.deleteMany();
        await tx.offboarded.deleteMany();
        await tx.compliance.deleteMany();

        // Insert employees
        for (const e of allEmps) {
          await tx.employee.create({ data: e });
        }
        for (const f of financeRows) await tx.finance.create({ data: f });
        for (const p of productivityRows) await tx.productivity.create({ data: p });
        for (const p of payrollRows) await tx.payroll.create({ data: p });
        for (const l of leaveRows) await tx.leave.create({ data: l });
        for (const a of attritionRows) await tx.attritionRisk.create({ data: a });
        for (const o of offboardedRows) await tx.offboarded.create({ data: o });
        for (const c of complianceRows) await tx.compliance.create({ data: c });
        for (const g of goalsRows) await tx.goal.create({ data: g });
        for (const tp of trainingProgramRows) await tx.trainingProgram.create({ data: tp });
        for (const te of trainingEnrollmentRows) await tx.trainingEnrollment.create({ data: te });
        for (const r of risksRows) await tx.risk.create({ data: r });
        for (const op of openPositionRows) await tx.openPosition.create({ data: op });
        for (const c of candidateRows) await tx.candidate.create({ data: c });
      },
      { timeout: 60000, maxWait: 60000 }
    );
  } catch (e: any) {
    return NextResponse.json(
      { error: `Database write failed: ${e.message}` },
      { status: 500 }
    );
  }

  return NextResponse.json({
    success: true,
    summary: {
      employees: allEmps.length,
      india: indiaEmps.length,
      us: usEmps.length,
      finance: financeRows.length,
      productivity: productivityRows.length,
      payroll: payrollRows.length,
      leave: leaveRows.length,
      attrition: attritionRows.length,
      offboarded: offboardedRows.length,
      compliance: complianceRows.length,
      goals: goalsRows.length,
      trainingPrograms: trainingProgramRows.length,
      trainingEnrollments: trainingEnrollmentRows.length,
      risks: risksRows.length,
      openPositions: openPositionRows.length,
      candidates: candidateRows.length,
    },
    detectedSheets: Object.keys(sheetMap),
  });
}
