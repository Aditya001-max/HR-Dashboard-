import UploadForm from "./UploadForm";

export default function ImportPage() {
  return (
    <div className="max-w-4xl mx-auto">
      <header className="mb-6 lg:mb-8">
        <div className="eyebrow text-ink/50">Data Import</div>
        <h1 className="serif text-3xl sm:text-4xl mt-2 font-light tracking-tightest leading-[1.1]">
          Upload your HR workbook
        </h1>
        <p className="mt-3 text-sm text-ink/60 max-w-2xl">
          Drop in an Excel file containing your employee data. The platform will parse it,
          replace the current dataset, and recompute all analytics automatically.
        </p>
      </header>

      <UploadForm />

      <section className="card mt-6">
        <div className="eyebrow text-ink/50 mb-3">Expected workbook structure</div>
        <p className="text-sm text-ink/65 leading-relaxed mb-4">
          The simplest path is to <strong>Download Excel</strong> from the dashboard, edit
          the rows you need, then upload the modified file back here. The importer matches
          column headers — exact name preferred but case-insensitive.
        </p>

        <div className="grid sm:grid-cols-2 gap-4 text-sm">
          <SheetSpec
            name="India Employees"
            required
            columns={[
              "Employee ID",
              "Name",
              "Department",
              "Designation",
              "Reporting Manager",
              "Skill / Tech Stack",
              "DOJ",
              "Employment Status",
              "LWD",
              "Intern End Date",
            ]}
          />
          <SheetSpec
            name="US Employees"
            required
            columns={[
              "Employee ID",
              "Name",
              "Department",
              "Designation",
              "Reporting Manager",
              "Skill / Tech Stack",
              "DOJ",
              "Employment Status",
              "Current Allocation %",
              "LWD",
              "Intern End Date",
            ]}
          />
          <SheetSpec
            name="Finance"
            columns={["Employee ID", "Annual (INR)", "Monthly (INR)", "Annual (USD)", "Monthly (USD)"]}
          />
          <SheetSpec
            name="Productivity"
            columns={["Employee ID", "Score", "Tasks Completed", "On-Time %"]}
          />
          <SheetSpec
            name="Payroll"
            columns={["Employee ID", "CTC", "Basic", "HRA", "Gross", "TDS", "Net Pay", "Currency"]}
          />
          <SheetSpec
            name="Leave & Attendance"
            columns={["Employee ID", "CL Balance", "SL Balance", "EL Balance", "Attendance %"]}
          />
          <SheetSpec
            name="Attrition Risk"
            columns={["Employee ID", "Total Score", "Risk Level", "Top Reason"]}
          />
          <SheetSpec
            name="Offboarded Resources"
            columns={["Employee ID", "Name", "Geo", "Department", "DOJ", "LWD", "Quarter", "Reason"]}
          />
        </div>

        <div className="mt-4 px-3 py-2.5 rounded-lg bg-accent-gold/10 text-xs text-ink/75 border border-accent-gold/30">
          <strong className="text-ink">Heads up:</strong> Uploading wipes the existing dataset and replaces it
          entirely. Download the current data first if you want a backup.
        </div>
      </section>
    </div>
  );
}

function SheetSpec({
  name,
  columns,
  required,
}: {
  name: string;
  columns: string[];
  required?: boolean;
}) {
  return (
    <div className="border border-ink/10 rounded-xl p-4 bg-cream">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-semibold text-ink">{name}</span>
        {required ? (
          <span className="pill pill-high">Required (or US)</span>
        ) : (
          <span className="pill pill-neutral">Optional</span>
        )}
      </div>
      <div className="text-xs text-ink/55 leading-relaxed">
        {columns.join(" · ")}
      </div>
    </div>
  );
}
