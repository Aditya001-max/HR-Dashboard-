import { PrismaClient } from "@prisma/client";
import bcrypt from "bcryptjs";
import fs from "node:fs";
import path from "node:path";

const prisma = new PrismaClient();

type AnyRec = Record<string, any>;

function readJson(p: string) {
  return JSON.parse(fs.readFileSync(p, "utf8"));
}

async function main() {
  const dataPath = path.join(process.cwd(), "source-code", "hr_data.json");
  const data = readJson(dataPath);

  console.log("→ Wiping existing data…");
  // Order matters due to FK constraints
  await prisma.candidate.deleteMany();
  await prisma.openPosition.deleteMany();
  await prisma.trainingEnrollment.deleteMany();
  await prisma.trainingProgram.deleteMany();
  await prisma.risk.deleteMany();
  await prisma.goal.deleteMany();
  await prisma.attritionRisk.deleteMany();
  await prisma.leave.deleteMany();
  await prisma.payroll.deleteMany();
  await prisma.productivity.deleteMany();
  await prisma.finance.deleteMany();
  await prisma.employee.deleteMany();
  await prisma.offboarded.deleteMany();
  await prisma.compliance.deleteMany();
  await prisma.user.deleteMany();

  // ---- Seed default HR admin user ----
  const passwordHash = await bcrypt.hash("demopassword", 10);
  await prisma.user.create({
    data: {
      email: "hr.admin@meridian.co",
      password: passwordHash,
      name: "HR Admin",
      role: "hr_admin",
    },
  });
  await prisma.user.create({
    data: {
      email: "damini.ai@divinehindu.in",
      password: await bcrypt.hash("welcome123", 10),
      name: "Damini",
      role: "hr_admin",
    },
  });
  console.log("✓ Seeded 2 users (login: hr.admin@meridian.co / demopassword)");

  // ---- Employees (India + US) ----
  const all: AnyRec[] = [
    ...data.india_employees.map((e: AnyRec) => ({ ...e, geo: "India" })),
    ...data.us_employees.map((e: AnyRec) => ({ ...e, geo: "US" })),
  ];

  for (const e of all) {
    await prisma.employee.create({
      data: {
        id: String(e.id),
        name: e.name,
        geo: e.geo,
        dept: e.dept,
        desig: e.desig,
        manager: e.manager ?? null,
        skill: e.skill ?? null,
        doj: e.doj,
        status: e.status,
        lwd: e.lwd ?? null,
        internEnd: e.intern_end ?? null,
        allocation: e.allocation != null ? String(e.allocation) : null,
      },
    });
  }
  console.log(`✓ Seeded ${all.length} employees`);

  // ---- Finance ----
  for (const f of data.finance) {
    await prisma.finance.create({
      data: {
        employeeId: String(f.id),
        annualInr: f.annual_inr ?? null,
        monthlyInr: f.monthly_inr ?? null,
        annualUsd: f.annual_usd ?? null,
        monthlyUsd: f.monthly_usd ?? null,
      },
    });
  }
  console.log(`✓ Seeded ${data.finance.length} finance rows`);

  // ---- Productivity ----
  for (const p of data.productivity) {
    await prisma.productivity.create({
      data: {
        employeeId: String(p.id),
        score: p.score,
        tasksCompleted: p.tasks_completed,
        onTimePct: p.on_time_pct,
      },
    });
  }
  console.log(`✓ Seeded ${data.productivity.length} productivity rows`);

  // ---- Payroll ----
  for (const p of data.payroll) {
    await prisma.payroll.create({
      data: {
        employeeId: String(p.id),
        ctc: p.ctc,
        basic: p.basic,
        hra: p.hra,
        special: p.special,
        gross: p.gross,
        pfEmp: p.pf_emp,
        pfEmr: p.pf_emr,
        esi: p.esi,
        pt: p.pt,
        tds: p.tds,
        net: p.net,
        currency: p.currency,
      },
    });
  }
  console.log(`✓ Seeded ${data.payroll.length} payroll rows`);

  // ---- Leaves ----
  for (const l of data.leaves) {
    await prisma.leave.create({
      data: {
        employeeId: String(l.id),
        clEntitled: l.cl_entitled,
        clUsed: l.cl_used,
        clBalance: l.cl_balance,
        slEntitled: l.sl_entitled,
        slUsed: l.sl_used,
        slBalance: l.sl_balance,
        elEntitled: l.el_entitled,
        elUsed: l.el_used,
        elBalance: l.el_balance,
        attendancePct: l.attendance_pct,
      },
    });
  }
  console.log(`✓ Seeded ${data.leaves.length} leave rows`);

  // ---- Attrition Risk ----
  for (const a of data.attrition_risk) {
    await prisma.attritionRisk.create({
      data: {
        employeeId: String(a.id),
        tenureDays: a.tenure_days,
        tenureScore: a.tenure_score,
        prodScore: a.prod_score,
        compScore: a.comp_score,
        otherScore: a.other_score,
        totalScore: a.total_score,
        riskLevel: a.risk_level,
        topReason: a.top_reason,
      },
    });
  }
  console.log(`✓ Seeded ${data.attrition_risk.length} attrition risk rows`);

  // ---- Goals ----
  for (const g of data.goals) {
    await prisma.goal.create({
      data: {
        id: String(g.goal_id),
        employeeId: String(g.emp_id),
        title: g.goal_title,
        description: g.description ?? null,
        unit: g.unit ?? null,
        target: g.target,
        actual: g.actual,
        weight: g.weight,
        achievementPct: g.achievement_pct,
        rating: g.rating ?? null,
        status: g.status,
      },
    });
  }
  console.log(`✓ Seeded ${data.goals.length} goals`);

  // ---- Training Programs ----
  for (const p of data.training_programs) {
    await prisma.trainingProgram.create({
      data: {
        id: String(p.train_id),
        title: p.title,
        category: p.category,
        durationHrs: p.duration_hrs,
        mandatory: !!p.mandatory,
        target: p.target ?? null,
      },
    });
  }
  console.log(`✓ Seeded ${data.training_programs.length} training programs`);

  // ---- Training Enrollments ----
  for (const en of data.training_enrollments) {
    await prisma.trainingEnrollment.create({
      data: {
        id: String(en.enroll_id),
        employeeId: String(en.emp_id),
        programId: String(en.train_id),
        completionPct: en.completion_pct,
        status: en.status,
      },
    });
  }
  console.log(`✓ Seeded ${data.training_enrollments.length} training enrollments`);

  // ---- Risks ----
  for (const r of data.risks) {
    await prisma.risk.create({
      data: {
        id: String(r.risk_id),
        employeeId: String(r.emp_id),
        category: r.category,
        level: r.level,
        raisedOn: r.raised_on,
        status: r.status,
        owner: r.owner ?? null,
        notes: r.notes ?? null,
      },
    });
  }
  console.log(`✓ Seeded ${data.risks.length} risks`);

  // ---- Open Positions ----
  for (const op of data.open_positions) {
    await prisma.openPosition.create({
      data: {
        id: String(op.pos_id),
        title: op.title,
        dept: op.dept,
        geo: op.geo,
        openings: op.openings,
        priority: op.priority,
        daysOpen: op.days_open,
      },
    });
  }
  console.log(`✓ Seeded ${data.open_positions.length} open positions`);

  // ---- Candidates ----
  for (const c of data.candidates) {
    await prisma.candidate.create({
      data: {
        id: String(c.cand_id),
        name: c.name,
        positionId: String(c.pos_id),
        stage: c.stage,
        daysInStage: c.days_in_stage,
        source: c.source,
        rating: c.rating ?? null,
      },
    });
  }
  console.log(`✓ Seeded ${data.candidates.length} candidates`);

  // ---- Compliance ----
  for (const c of data.compliance) {
    await prisma.compliance.create({
      data: {
        id: String(c.comp_id),
        title: c.title,
        category: c.category,
        geo: c.geo,
        dueDate: c.due_date,
        frequency: c.frequency,
        authority: c.authority,
        status: c.status,
      },
    });
  }
  console.log(`✓ Seeded ${data.compliance.length} compliance events`);

  // ---- Offboarded ----
  for (const o of data.offboarded) {
    await prisma.offboarded.create({
      data: {
        id: String(o.id),
        name: o.name,
        geo: o.geo,
        dept: o.dept,
        desig: o.desig,
        doj: o.doj,
        lwd: o.lwd,
        quarter: o.quarter,
        reason: o.reason,
        tenureYears: o.tenure_years,
      },
    });
  }
  console.log(`✓ Seeded ${data.offboarded.length} offboarded records`);

  console.log("\n✅ Seed complete.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
