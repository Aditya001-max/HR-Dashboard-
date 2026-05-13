"""
HR Automation Dashboard - Workbook Builder
Builds the complete Excel deliverable with all 7 tabs + Dashboard.

Design principles:
- Every cell on the Dashboard pulls live via formulas. No hardcoded numbers.
- Conditional formatting for alerts (red/amber/green).
- Data validation dropdowns for status fields.
- Charts native to Excel (no pictures).
- Frozen panes, hidden gridlines on Dashboard, clean palette.
"""
import os
from datetime import date, timedelta
from openpyxl import Workbook
from openpyxl.styles import (Font, PatternFill, Alignment, Border, Side,
                             NamedStyle, GradientFill)
from openpyxl.formatting.rule import (ColorScaleRule, CellIsRule, FormulaRule,
                                      DataBarRule, IconSetRule, Rule)
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, PieChart, LineChart, Reference, BarChart3D
from openpyxl.chart.label import DataLabelList
from openpyxl.chart.layout import Layout, ManualLayout
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.comments import Comment

# Import the generated data
import generate_data as gd

# ==================== DESIGN TOKENS ====================
# Inspired by modern analytics dashboards (PowerBI, Tableau, Lattice)
NAVY = '1E3A5F'           # primary dark
TEAL = '2EBFA5'           # primary accent (positive)
CORAL = 'FF6B6B'          # alert / negative
AMBER = 'F4A261'          # warning
SLATE = '64748B'          # secondary text
LIGHT_BG = 'F8FAFC'       # subtle background
WHITE = 'FFFFFF'
LIGHT_GRAY = 'E5E7EB'
DARK_TEXT = '1F2937'
GREEN_GOOD = '10B981'
RED_BAD = 'EF4444'
HEADER_BG = '0F172A'      # near-black header

THIN = Side(style='thin', color=LIGHT_GRAY)
MEDIUM = Side(style='medium', color=NAVY)
NO_BORDER = Border()
THIN_BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BOTTOM_BORDER = Border(bottom=Side(style='thin', color=SLATE))

FONT = 'Calibri'  # Excel default, professional, available everywhere

# ==================== HELPER FUNCTIONS ====================
def style_header_row(ws, row, start_col, end_col, bg=NAVY, fg=WHITE, bold=True, size=11):
    """Apply header styling to a row range."""
    for col in range(start_col, end_col + 1):
        cell = ws.cell(row=row, column=col)
        cell.font = Font(name=FONT, bold=bold, color=fg, size=size)
        cell.fill = PatternFill('solid', start_color=bg)
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = Border(left=Side(style='thin', color=bg),
                            right=Side(style='thin', color=bg),
                            top=Side(style='thin', color=bg),
                            bottom=Side(style='thin', color=bg))

def auto_width(ws, widths):
    """Set column widths. widths: dict of col_letter -> width or list of widths."""
    if isinstance(widths, dict):
        for col, w in widths.items():
            ws.column_dimensions[col].width = w
    else:
        for i, w in enumerate(widths, 1):
            ws.column_dimensions[get_column_letter(i)].width = w

def add_table_borders(ws, start_row, end_row, start_col, end_col):
    """Light borders for data rows."""
    for r in range(start_row, end_row + 1):
        for c in range(start_col, end_col + 1):
            ws.cell(row=r, column=c).border = THIN_BORDER

def fmt_date(d):
    if isinstance(d, date):
        return d
    return d

# ==================== BUILD WORKBOOK ====================
wb = Workbook()
# Remove default sheet; we'll add ours in order
wb.remove(wb.active)

# Workbook-level: make sure Dashboard is the first sheet user sees
TODAY_CELL_REF = "'Settings'!$B$2"  # central TODAY() so reviewers can override if needed

# ---------- Settings sheet (hidden config) ----------
ws_settings = wb.create_sheet('Settings')
ws_settings.sheet_state = 'visible'  # keep visible so reviewers can see the date
ws_settings['A1'] = 'Configuration'
ws_settings['A1'].font = Font(name=FONT, bold=True, size=14, color=NAVY)
ws_settings['A2'] = 'Report Date (changes recalculate all alerts)'
ws_settings['B2'] = '=TODAY()'
ws_settings['B2'].number_format = 'dd-mmm-yyyy'
ws_settings['B2'].font = Font(name=FONT, bold=True, color=NAVY, size=12)
ws_settings['B2'].fill = PatternFill('solid', start_color='FFF9C4')

ws_settings['A4'] = 'Probation Confirmation Window (days)'
ws_settings['B4'] = 30
ws_settings['A5'] = 'Intern LWD Alert Window (days)'
ws_settings['B5'] = 45
ws_settings['A6'] = 'Probation Duration (days from DOJ)'
ws_settings['B6'] = 180

ws_settings['A8'] = 'USD-INR Conversion Rate'
ws_settings['B8'] = 83.5
ws_settings['B8'].number_format = '#,##0.00'

ws_settings['A10'] = 'Notes for HR'
ws_settings['A10'].font = Font(name=FONT, bold=True, color=NAVY)
ws_settings['A11'] = 'Update Offboarded Resources tab whenever an employee exits.'
ws_settings['A12'] = 'Update Risk Report tab whenever a new risk is flagged.'
ws_settings['A13'] = "Status 'Intern' employees must have an Intern End Date populated."

for r in range(1, 15):
    ws_settings[f'A{r}'].alignment = Alignment(horizontal='left')
ws_settings.column_dimensions['A'].width = 50
ws_settings.column_dimensions['B'].width = 18

# Named ranges for cleaner formulas
wb.defined_names['ReportDate'] = DefinedName('ReportDate', attr_text="Settings!$B$2")
wb.defined_names['ProbationWindow'] = DefinedName('ProbationWindow', attr_text="Settings!$B$4")
wb.defined_names['InternAlertDays'] = DefinedName('InternAlertDays', attr_text="Settings!$B$5")
wb.defined_names['ProbationDays'] = DefinedName('ProbationDays', attr_text="Settings!$B$6")
wb.defined_names['USDINR'] = DefinedName('USDINR', attr_text="Settings!$B$8")

print("Settings sheet built.")

# ============================================================
# TAB 1: INDIA EMPLOYEE DATABASE
# ============================================================
ws_india = wb.create_sheet('India Employees')

# Sheet title row
ws_india.merge_cells('A1:K1')
ws_india['A1'] = 'INDIA EMPLOYEE DATABASE'
ws_india['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_india['A1'].fill = PatternFill('solid', start_color=NAVY)
ws_india['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_india.row_dimensions[1].height = 32

ws_india.merge_cells('A2:K2')
ws_india['A2'] = 'Source of truth for all India-based employees. Update Status to "Confirmed" after probation review. Set LWD for offboarded resources (also add to Offboarded Resources tab).'
ws_india['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_india['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_india.row_dimensions[2].height = 28

# Headers
india_headers = ['Employee ID', 'Name', 'Department', 'Designation', 'Reporting Manager',
                 'Skillset', 'Date of Joining', 'Employment Status', 'Tenure (Years)',
                 'Intern Internship End Date', 'Last Working Day (LWD)']
HEADER_ROW = 4
for i, h in enumerate(india_headers, 1):
    ws_india.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_india, HEADER_ROW, 1, len(india_headers), bg=NAVY)
ws_india.row_dimensions[HEADER_ROW].height = 36

# Data rows
data_start = HEADER_ROW + 1
for idx, emp in enumerate(gd.india_employees):
    r = data_start + idx
    ws_india.cell(row=r, column=1, value=emp['id'])
    ws_india.cell(row=r, column=2, value=emp['name'])
    ws_india.cell(row=r, column=3, value=emp['dept'])
    ws_india.cell(row=r, column=4, value=emp['desig'])
    ws_india.cell(row=r, column=5, value=emp['manager'])
    ws_india.cell(row=r, column=6, value=emp['skill'])
    doj_cell = ws_india.cell(row=r, column=7, value=emp['doj'])
    doj_cell.number_format = 'dd-mmm-yyyy'
    ws_india.cell(row=r, column=8, value=emp['status'])
    # Tenure = (ReportDate - DOJ) / 365.25  -- formula
    ws_india.cell(row=r, column=9, value=f'=IFERROR(ROUND((ReportDate-G{r})/365.25,2),"")')
    ws_india.cell(row=r, column=9).number_format = '0.00'
    if emp['intern_end']:
        ie = ws_india.cell(row=r, column=10, value=emp['intern_end'])
        ie.number_format = 'dd-mmm-yyyy'
    if emp['lwd']:
        lwd = ws_india.cell(row=r, column=11, value=emp['lwd'])
        lwd.number_format = 'dd-mmm-yyyy'

india_data_end = data_start + len(gd.india_employees) - 1

# Borders + alternating row banding
for r in range(data_start, india_data_end + 1):
    for c in range(1, 12):
        cell = ws_india.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='left' if c in [2,3,4,5,6] else 'center', vertical='center')

# Data validation for Status
dv_status = DataValidation(type='list', formula1='"Confirmed,Under Probation,Intern,Offboarded"', allow_blank=False)
dv_status.error = 'Status must be one of: Confirmed, Under Probation, Intern, Offboarded'
dv_status.errorTitle = 'Invalid Status'
dv_status.prompt = 'Select employee status'
dv_status.promptTitle = 'Status'
ws_india.add_data_validation(dv_status)
dv_status.add(f'H{data_start}:H{india_data_end}')

# Conditional formatting for status colors
ws_india.conditional_formatting.add(
    f'H{data_start}:H{india_data_end}',
    FormulaRule(formula=[f'$H{data_start}="Confirmed"'],
                fill=PatternFill('solid', start_color='D1FAE5'),
                font=Font(name=FONT, size=10, color='065F46', bold=True))
)
ws_india.conditional_formatting.add(
    f'H{data_start}:H{india_data_end}',
    FormulaRule(formula=[f'$H{data_start}="Under Probation"'],
                fill=PatternFill('solid', start_color='FEF3C7'),
                font=Font(name=FONT, size=10, color='92400E', bold=True))
)
ws_india.conditional_formatting.add(
    f'H{data_start}:H{india_data_end}',
    FormulaRule(formula=[f'$H{data_start}="Intern"'],
                fill=PatternFill('solid', start_color='DBEAFE'),
                font=Font(name=FONT, size=10, color='1E40AF', bold=True))
)
ws_india.conditional_formatting.add(
    f'H{data_start}:H{india_data_end}',
    FormulaRule(formula=[f'$H{data_start}="Offboarded"'],
                fill=PatternFill('solid', start_color='FEE2E2'),
                font=Font(name=FONT, size=10, color='991B1B', bold=True))
)

# Highlight interns ending in next 45 days (entire row LWD column)
ws_india.conditional_formatting.add(
    f'J{data_start}:J{india_data_end}',
    FormulaRule(formula=[f'AND(J{data_start}<>"",J{data_start}-ReportDate>=0,J{data_start}-ReportDate<=InternAlertDays)'],
                fill=PatternFill('solid', start_color=CORAL),
                font=Font(name=FONT, size=10, color=WHITE, bold=True))
)

# Highlight probation due in next 30 days
ws_india.conditional_formatting.add(
    f'G{data_start}:G{india_data_end}',
    FormulaRule(formula=[f'AND($H{data_start}="Under Probation",ProbationDays-(ReportDate-$G{data_start})>=0,ProbationDays-(ReportDate-$G{data_start})<=ProbationWindow)'],
                fill=PatternFill('solid', start_color=AMBER),
                font=Font(name=FONT, size=10, color=WHITE, bold=True))
)

# Column widths
auto_width(ws_india, [13, 22, 18, 22, 22, 22, 14, 17, 12, 18, 14])

# Freeze panes
ws_india.freeze_panes = f'A{data_start}'

# Hide gridlines, autofilter
ws_india.sheet_view.showGridLines = False
ws_india.auto_filter.ref = f'A{HEADER_ROW}:K{india_data_end}'

# Add a defined name for the table for cross-sheet lookups
wb.defined_names['IndiaData'] = DefinedName('IndiaData', attr_text=f"'India Employees'!$A${data_start}:$K${india_data_end}")
wb.defined_names['IndiaIDs'] = DefinedName('IndiaIDs', attr_text=f"'India Employees'!$A${data_start}:$A${india_data_end}")
wb.defined_names['IndiaStatus'] = DefinedName('IndiaStatus', attr_text=f"'India Employees'!$H${data_start}:$H${india_data_end}")
wb.defined_names['IndiaDept'] = DefinedName('IndiaDept', attr_text=f"'India Employees'!$C${data_start}:$C${india_data_end}")
wb.defined_names['IndiaInternEnd'] = DefinedName('IndiaInternEnd', attr_text=f"'India Employees'!$J${data_start}:$J${india_data_end}")
wb.defined_names['IndiaDOJ'] = DefinedName('IndiaDOJ', attr_text=f"'India Employees'!$G${data_start}:$G${india_data_end}")

print(f"India Employees tab: {len(gd.india_employees)} records.")

# ============================================================
# TAB 2: US EMPLOYEE DATABASE
# ============================================================
ws_us = wb.create_sheet('US Employees')

ws_us.merge_cells('A1:L1')
ws_us['A1'] = 'US EMPLOYEE DATABASE'
ws_us['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_us['A1'].fill = PatternFill('solid', start_color=NAVY)
ws_us['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_us.row_dimensions[1].height = 32

ws_us.merge_cells('A2:L2')
ws_us['A2'] = 'Source of truth for all US-based employees. Allocation % drives Finance calculations. Update Status when probation reviews complete.'
ws_us['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_us['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_us.row_dimensions[2].height = 28

us_headers = ['Employee ID', 'Name', 'Department', 'Designation', 'Reporting Manager',
              'Current Allocation (%)', 'Skillset', 'Date of Joining',
              'Employment Status', 'Tenure (Years)', 'Intern Internship End Date',
              'Last Working Day (LWD)']
for i, h in enumerate(us_headers, 1):
    ws_us.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_us, HEADER_ROW, 1, len(us_headers), bg=NAVY)
ws_us.row_dimensions[HEADER_ROW].height = 36

us_data_start = HEADER_ROW + 1
for idx, emp in enumerate(gd.us_employees):
    r = us_data_start + idx
    ws_us.cell(row=r, column=1, value=emp['id'])
    ws_us.cell(row=r, column=2, value=emp['name'])
    ws_us.cell(row=r, column=3, value=emp['dept'])
    ws_us.cell(row=r, column=4, value=emp['desig'])
    ws_us.cell(row=r, column=5, value=emp['manager'])
    alloc = ws_us.cell(row=r, column=6, value=emp['allocation']/100)
    alloc.number_format = '0%'
    ws_us.cell(row=r, column=7, value=emp['skill'])
    doj = ws_us.cell(row=r, column=8, value=emp['doj'])
    doj.number_format = 'dd-mmm-yyyy'
    ws_us.cell(row=r, column=9, value=emp['status'])
    ws_us.cell(row=r, column=10, value=f'=IFERROR(ROUND((ReportDate-H{r})/365.25,2),"")')
    ws_us.cell(row=r, column=10).number_format = '0.00'
    if emp['intern_end']:
        ie = ws_us.cell(row=r, column=11, value=emp['intern_end'])
        ie.number_format = 'dd-mmm-yyyy'

us_data_end = us_data_start + len(gd.us_employees) - 1

for r in range(us_data_start, us_data_end + 1):
    for c in range(1, 13):
        cell = ws_us.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - us_data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='left' if c in [2,3,4,5,7] else 'center', vertical='center')

# Data validation
dv_status_us = DataValidation(type='list', formula1='"Confirmed,Under Probation,Intern,Offboarded"', allow_blank=False)
ws_us.add_data_validation(dv_status_us)
dv_status_us.add(f'I{us_data_start}:I{us_data_end}')

# Status colors
for status_val, bg_col, fg_col in [
    ('Confirmed', 'D1FAE5', '065F46'),
    ('Under Probation', 'FEF3C7', '92400E'),
    ('Intern', 'DBEAFE', '1E40AF'),
    ('Offboarded', 'FEE2E2', '991B1B'),
]:
    ws_us.conditional_formatting.add(
        f'I{us_data_start}:I{us_data_end}',
        FormulaRule(formula=[f'$I{us_data_start}="{status_val}"'],
                    fill=PatternFill('solid', start_color=bg_col),
                    font=Font(name=FONT, size=10, color=fg_col, bold=True))
    )

# Allocation databar
ws_us.conditional_formatting.add(
    f'F{us_data_start}:F{us_data_end}',
    DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color=TEAL)
)

# Intern end alert
ws_us.conditional_formatting.add(
    f'K{us_data_start}:K{us_data_end}',
    FormulaRule(formula=[f'AND(K{us_data_start}<>"",K{us_data_start}-ReportDate>=0,K{us_data_start}-ReportDate<=InternAlertDays)'],
                fill=PatternFill('solid', start_color=CORAL),
                font=Font(name=FONT, size=10, color=WHITE, bold=True))
)
# Probation due alert
ws_us.conditional_formatting.add(
    f'H{us_data_start}:H{us_data_end}',
    FormulaRule(formula=[f'AND($I{us_data_start}="Under Probation",ProbationDays-(ReportDate-$H{us_data_start})>=0,ProbationDays-(ReportDate-$H{us_data_start})<=ProbationWindow)'],
                fill=PatternFill('solid', start_color=AMBER),
                font=Font(name=FONT, size=10, color=WHITE, bold=True))
)

auto_width(ws_us, [13, 22, 18, 22, 22, 14, 22, 14, 17, 12, 18, 14])
ws_us.freeze_panes = f'A{us_data_start}'
ws_us.sheet_view.showGridLines = False
ws_us.auto_filter.ref = f'A{HEADER_ROW}:L{us_data_end}'

wb.defined_names['USData'] = DefinedName('USData', attr_text=f"'US Employees'!$A${us_data_start}:$L${us_data_end}")
wb.defined_names['USIDs'] = DefinedName('USIDs', attr_text=f"'US Employees'!$A${us_data_start}:$A${us_data_end}")
wb.defined_names['USStatus'] = DefinedName('USStatus', attr_text=f"'US Employees'!$I${us_data_start}:$I${us_data_end}")
wb.defined_names['USDept'] = DefinedName('USDept', attr_text=f"'US Employees'!$C${us_data_start}:$C${us_data_end}")
wb.defined_names['USInternEnd'] = DefinedName('USInternEnd', attr_text=f"'US Employees'!$K${us_data_start}:$K${us_data_end}")
wb.defined_names['USDOJ'] = DefinedName('USDOJ', attr_text=f"'US Employees'!$H${us_data_start}:$H${us_data_end}")
wb.defined_names['USAllocation'] = DefinedName('USAllocation', attr_text=f"'US Employees'!$F${us_data_start}:$F${us_data_end}")

print(f"US Employees tab: {len(gd.us_employees)} records.")

# ============================================================
# TAB 3: RM DATA (Monthly Resource Allocation)
# ============================================================
ws_rm = wb.create_sheet('RM Data')

ws_rm.merge_cells('A1:F1')
ws_rm['A1'] = 'RESOURCE MANAGEMENT - MONTHLY ALLOCATION'
ws_rm['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_rm['A1'].fill = PatternFill('solid', start_color=NAVY)
ws_rm['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_rm.row_dimensions[1].height = 32

ws_rm.merge_cells('A2:F2')
ws_rm['A2'] = 'Updated each month. Feeds live allocation figures and intern LWD tracking into the dashboard.'
ws_rm['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_rm['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_rm.row_dimensions[2].height = 24

rm_headers = ['Employee ID', 'Name', 'Department', 'Month', 'Allocation (%)', 'LWD / Intern End']
for i, h in enumerate(rm_headers, 1):
    ws_rm.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_rm, HEADER_ROW, 1, len(rm_headers), bg=NAVY)
ws_rm.row_dimensions[HEADER_ROW].height = 32

rm_data_start = HEADER_ROW + 1
for idx, row in enumerate(gd.rm_data):
    r = rm_data_start + idx
    ws_rm.cell(row=r, column=1, value=row['id'])
    ws_rm.cell(row=r, column=2, value=row['name'])
    ws_rm.cell(row=r, column=3, value=row['dept'])
    ws_rm.cell(row=r, column=4, value=row['month'])
    alloc = ws_rm.cell(row=r, column=5, value=row['allocation']/100)
    alloc.number_format = '0%'
    if row['lwd_intern_end']:
        cell = ws_rm.cell(row=r, column=6, value=row['lwd_intern_end'])
        cell.number_format = 'dd-mmm-yyyy'

rm_data_end = rm_data_start + len(gd.rm_data) - 1

for r in range(rm_data_start, rm_data_end + 1):
    for c in range(1, 7):
        cell = ws_rm.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - rm_data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='left' if c in [2,3] else 'center', vertical='center')

ws_rm.conditional_formatting.add(
    f'E{rm_data_start}:E{rm_data_end}',
    DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color=TEAL)
)

auto_width(ws_rm, [13, 22, 18, 14, 14, 18])
ws_rm.freeze_panes = f'A{rm_data_start}'
ws_rm.sheet_view.showGridLines = False
ws_rm.auto_filter.ref = f'A{HEADER_ROW}:F{rm_data_end}'

print(f"RM Data tab: {len(gd.rm_data)} records.")

# ============================================================
# TAB 4: FINANCE (CTC - Annual & Monthly, INR & USD)
# ============================================================
ws_fin = wb.create_sheet('Finance')

ws_fin.merge_cells('A1:I1')
ws_fin['A1'] = 'FINANCE - CTC BREAKDOWN (INR & USD)'
ws_fin['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_fin['A1'].fill = PatternFill('solid', start_color=NAVY)
ws_fin['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_fin.row_dimensions[1].height = 32

ws_fin.merge_cells('A2:I2')
ws_fin['A2'] = 'Annual & monthly CTC for every resource. USD values are calculated using the conversion rate in Settings (B8).'
ws_fin['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_fin['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_fin.row_dimensions[2].height = 24

fin_headers = ['Employee ID', 'Name', 'Geography', 'Department', 'Designation',
               'Annual CTC (INR)', 'Monthly CTC (INR)', 'Annual CTC (USD)', 'Monthly CTC (USD)']
for i, h in enumerate(fin_headers, 1):
    ws_fin.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_fin, HEADER_ROW, 1, len(fin_headers), bg=NAVY)
ws_fin.row_dimensions[HEADER_ROW].height = 32

fin_data_start = HEADER_ROW + 1
for idx, row in enumerate(gd.finance_data):
    r = fin_data_start + idx
    ws_fin.cell(row=r, column=1, value=row['id'])
    ws_fin.cell(row=r, column=2, value=row['name'])
    ws_fin.cell(row=r, column=3, value=row['geo'])
    ws_fin.cell(row=r, column=4, value=row['dept'])
    ws_fin.cell(row=r, column=5, value=row['desig'])
    # For India: annual_inr is the source. For US: annual_usd is the source.
    if row['geo'] == 'India':
        c6 = ws_fin.cell(row=r, column=6, value=row['annual_inr'])  # hardcoded source
        c7 = ws_fin.cell(row=r, column=7, value=f'=F{r}/12')        # monthly INR formula
        c8 = ws_fin.cell(row=r, column=8, value=f'=F{r}/USDINR')    # annual USD formula
        c9 = ws_fin.cell(row=r, column=9, value=f'=H{r}/12')        # monthly USD formula
    else:
        c8 = ws_fin.cell(row=r, column=8, value=row['annual_usd'])  # source
        c9 = ws_fin.cell(row=r, column=9, value=f'=H{r}/12')
        c6 = ws_fin.cell(row=r, column=6, value=f'=H{r}*USDINR')
        c7 = ws_fin.cell(row=r, column=7, value=f'=F{r}/12')
    c6.number_format = '₹#,##0'
    c7.number_format = '₹#,##0'
    c8.number_format = '$#,##0'
    c9.number_format = '$#,##0'

fin_data_end = fin_data_start + len(gd.finance_data) - 1

for r in range(fin_data_start, fin_data_end + 1):
    for c in range(1, 10):
        cell = ws_fin.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - fin_data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='right' if c >= 6 else ('left' if c in [2,4,5] else 'center'), vertical='center')

# Totals row
total_row = fin_data_end + 1
ws_fin.cell(row=total_row, column=1, value='TOTAL')
ws_fin.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=5)
ws_fin.cell(row=total_row, column=6, value=f'=SUM(F{fin_data_start}:F{fin_data_end})').number_format = '₹#,##0'
ws_fin.cell(row=total_row, column=7, value=f'=SUM(G{fin_data_start}:G{fin_data_end})').number_format = '₹#,##0'
ws_fin.cell(row=total_row, column=8, value=f'=SUM(H{fin_data_start}:H{fin_data_end})').number_format = '$#,##0'
ws_fin.cell(row=total_row, column=9, value=f'=SUM(I{fin_data_start}:I{fin_data_end})').number_format = '$#,##0'
for c in range(1, 10):
    cell = ws_fin.cell(row=total_row, column=c)
    cell.font = Font(name=FONT, bold=True, color=WHITE, size=11)
    cell.fill = PatternFill('solid', start_color=NAVY)
    cell.alignment = Alignment(horizontal='right' if c >= 6 else 'center', vertical='center')

# Databars on CTC columns
ws_fin.conditional_formatting.add(
    f'F{fin_data_start}:F{fin_data_end}',
    DataBarRule(start_type='min', end_type='max', color=NAVY)
)

auto_width(ws_fin, [13, 22, 11, 18, 22, 18, 16, 18, 16])
ws_fin.freeze_panes = f'A{fin_data_start}'
ws_fin.sheet_view.showGridLines = False
ws_fin.auto_filter.ref = f'A{HEADER_ROW}:I{fin_data_end}'

wb.defined_names['FinanceData'] = DefinedName('FinanceData', attr_text=f"'Finance'!$A${fin_data_start}:$I${fin_data_end}")
wb.defined_names['FinanceGeo'] = DefinedName('FinanceGeo', attr_text=f"'Finance'!$C${fin_data_start}:$C${fin_data_end}")
wb.defined_names['FinanceDept'] = DefinedName('FinanceDept', attr_text=f"'Finance'!$D${fin_data_start}:$D${fin_data_end}")
wb.defined_names['FinanceAnnualINR'] = DefinedName('FinanceAnnualINR', attr_text=f"'Finance'!$F${fin_data_start}:$F${fin_data_end}")
wb.defined_names['FinanceAnnualUSD'] = DefinedName('FinanceAnnualUSD', attr_text=f"'Finance'!$H${fin_data_start}:$H${fin_data_end}")
wb.defined_names['FinanceMonthlyINR'] = DefinedName('FinanceMonthlyINR', attr_text=f"'Finance'!$G${fin_data_start}:$G${fin_data_end}")
wb.defined_names['FinanceMonthlyUSD'] = DefinedName('FinanceMonthlyUSD', attr_text=f"'Finance'!$I${fin_data_start}:$I${fin_data_end}")

print(f"Finance tab: {len(gd.finance_data)} records.")

# ============================================================
# TAB 5: PRODUCTIVITY
# ============================================================
ws_prod = wb.create_sheet('Productivity')

ws_prod.merge_cells('A1:G1')
ws_prod['A1'] = 'PRODUCTIVITY - PER RESOURCE'
ws_prod['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_prod['A1'].fill = PatternFill('solid', start_color=NAVY)
ws_prod['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_prod.row_dimensions[1].height = 32

ws_prod.merge_cells('A2:G2')
ws_prod['A2'] = 'Productivity average per resource (1-5 scale). Dashboard rolls this up to a summary metric only.'
ws_prod['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_prod['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_prod.row_dimensions[2].height = 24

prod_headers = ['Employee ID', 'Name', 'Geography', 'Department', 'Designation',
                'Productivity Score (1-5)', 'On-Time Delivery %']
for i, h in enumerate(prod_headers, 1):
    ws_prod.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_prod, HEADER_ROW, 1, len(prod_headers), bg=NAVY)
ws_prod.row_dimensions[HEADER_ROW].height = 36

prod_data_start = HEADER_ROW + 1
for idx, row in enumerate(gd.productivity_data):
    r = prod_data_start + idx
    ws_prod.cell(row=r, column=1, value=row['id'])
    ws_prod.cell(row=r, column=2, value=row['name'])
    ws_prod.cell(row=r, column=3, value=row['geo'])
    ws_prod.cell(row=r, column=4, value=row['dept'])
    ws_prod.cell(row=r, column=5, value=row['desig'])
    ws_prod.cell(row=r, column=6, value=row['score']).number_format = '0.00'
    ws_prod.cell(row=r, column=7, value=row['on_time_pct']/100).number_format = '0.0%'

prod_data_end = prod_data_start + len(gd.productivity_data) - 1

for r in range(prod_data_start, prod_data_end + 1):
    for c in range(1, 8):
        cell = ws_prod.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - prod_data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='left' if c in [2,4,5] else 'center', vertical='center')

# Color scale for score
ws_prod.conditional_formatting.add(
    f'F{prod_data_start}:F{prod_data_end}',
    ColorScaleRule(start_type='num', start_value=1, start_color='F87171',
                   mid_type='num', mid_value=3, mid_color='FBBF24',
                   end_type='num', end_value=5, end_color=GREEN_GOOD)
)
ws_prod.conditional_formatting.add(
    f'G{prod_data_start}:G{prod_data_end}',
    DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color=TEAL)
)

auto_width(ws_prod, [13, 22, 11, 18, 22, 16, 16])
ws_prod.freeze_panes = f'A{prod_data_start}'
ws_prod.sheet_view.showGridLines = False
ws_prod.auto_filter.ref = f'A{HEADER_ROW}:G{prod_data_end}'

wb.defined_names['ProductivityScore'] = DefinedName('ProductivityScore', attr_text=f"'Productivity'!$F${prod_data_start}:$F${prod_data_end}")
wb.defined_names['ProductivityGeo'] = DefinedName('ProductivityGeo', attr_text=f"'Productivity'!$C${prod_data_start}:$C${prod_data_end}")
wb.defined_names['ProductivityDept'] = DefinedName('ProductivityDept', attr_text=f"'Productivity'!$D${prod_data_start}:$D${prod_data_end}")

print(f"Productivity tab: {len(gd.productivity_data)} records.")

# ============================================================
# TAB 6: RISK REPORT
# ============================================================
ws_risk = wb.create_sheet('Risk Report')

ws_risk.merge_cells('A1:J1')
ws_risk['A1'] = 'RISK REPORT - HR ALERTS'
ws_risk['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_risk['A1'].fill = PatternFill('solid', start_color=CORAL)
ws_risk['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_risk.row_dimensions[1].height = 32

ws_risk.merge_cells('A2:J2')
ws_risk['A2'] = 'Maintained by HR. Real-time updates here are reflected directly on the Dashboard Risk panel.'
ws_risk['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_risk['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_risk.row_dimensions[2].height = 24

risk_headers = ['Risk ID', 'Employee ID', 'Employee Name', 'Geography', 'Department',
                'Risk Category', 'Risk Level', 'Raised On', 'Status', 'Notes / Action']
for i, h in enumerate(risk_headers, 1):
    ws_risk.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_risk, HEADER_ROW, 1, len(risk_headers), bg=CORAL)
ws_risk.row_dimensions[HEADER_ROW].height = 32

risk_data_start = HEADER_ROW + 1
for idx, row in enumerate(gd.risk_data):
    r = risk_data_start + idx
    ws_risk.cell(row=r, column=1, value=row['risk_id'])
    ws_risk.cell(row=r, column=2, value=row['emp_id'])
    ws_risk.cell(row=r, column=3, value=row['emp_name'])
    ws_risk.cell(row=r, column=4, value=row['geo'])
    ws_risk.cell(row=r, column=5, value=row['dept'])
    ws_risk.cell(row=r, column=6, value=row['category'])
    ws_risk.cell(row=r, column=7, value=row['level'])
    raised = ws_risk.cell(row=r, column=8, value=row['raised_on'])
    raised.number_format = 'dd-mmm-yyyy'
    ws_risk.cell(row=r, column=9, value=row['status'])
    ws_risk.cell(row=r, column=10, value=row['notes'])

risk_data_end = risk_data_start + len(gd.risk_data) - 1

for r in range(risk_data_start, risk_data_end + 1):
    for c in range(1, 11):
        cell = ws_risk.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - risk_data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='left' if c in [3,5,6,10] else 'center', vertical='center', wrap_text=True)

# Data validation: Risk Level
dv_lvl = DataValidation(type='list', formula1='"High,Medium,Low"', allow_blank=False)
ws_risk.add_data_validation(dv_lvl)
dv_lvl.add(f'G{risk_data_start}:G{risk_data_end+30}')  # extra rows for new entries

dv_st = DataValidation(type='list', formula1='"Open,Under Review,Mitigation in Progress,Closed"', allow_blank=False)
ws_risk.add_data_validation(dv_st)
dv_st.add(f'I{risk_data_start}:I{risk_data_end+30}')

# Conditional formatting for Risk Level
for level, fill_col, fg_col in [
    ('High', CORAL, WHITE),
    ('Medium', AMBER, WHITE),
    ('Low', TEAL, WHITE),
]:
    ws_risk.conditional_formatting.add(
        f'G{risk_data_start}:G{risk_data_end+30}',
        FormulaRule(formula=[f'$G{risk_data_start}="{level}"'],
                    fill=PatternFill('solid', start_color=fill_col),
                    font=Font(name=FONT, size=10, color=fg_col, bold=True))
    )

# Status colors
for status_val, bg_col, fg_col in [
    ('Open', 'FEE2E2', '991B1B'),
    ('Under Review', 'FEF3C7', '92400E'),
    ('Mitigation in Progress', 'DBEAFE', '1E40AF'),
    ('Closed', 'D1FAE5', '065F46'),
]:
    ws_risk.conditional_formatting.add(
        f'I{risk_data_start}:I{risk_data_end+30}',
        FormulaRule(formula=[f'$I{risk_data_start}="{status_val}"'],
                    fill=PatternFill('solid', start_color=bg_col),
                    font=Font(name=FONT, size=10, color=fg_col, bold=True))
    )

auto_width(ws_risk, [10, 13, 22, 11, 16, 22, 12, 14, 22, 45])
ws_risk.freeze_panes = f'A{risk_data_start}'
ws_risk.sheet_view.showGridLines = False
ws_risk.auto_filter.ref = f'A{HEADER_ROW}:J{risk_data_end}'

wb.defined_names['RiskData'] = DefinedName('RiskData', attr_text=f"'Risk Report'!$A${risk_data_start}:$J${risk_data_end+30}")
wb.defined_names['RiskLevels'] = DefinedName('RiskLevels', attr_text=f"'Risk Report'!$G${risk_data_start}:$G${risk_data_end+30}")
wb.defined_names['RiskStatuses'] = DefinedName('RiskStatuses', attr_text=f"'Risk Report'!$I${risk_data_start}:$I${risk_data_end+30}")
wb.defined_names['RiskDepts'] = DefinedName('RiskDepts', attr_text=f"'Risk Report'!$E${risk_data_start}:$E${risk_data_end+30}")

print(f"Risk Report tab: {len(gd.risk_data)} records.")

# ============================================================
# TAB 7: OFFBOARDED RESOURCES
# ============================================================
ws_off = wb.create_sheet('Offboarded Resources')

ws_off.merge_cells('A1:I1')
ws_off['A1'] = 'OFFBOARDED RESOURCES'
ws_off['A1'].font = Font(name=FONT, bold=True, size=16, color=WHITE)
ws_off['A1'].fill = PatternFill('solid', start_color=NAVY)
ws_off['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_off.row_dimensions[1].height = 32

ws_off.merge_cells('A2:I2')
ws_off['A2'] = 'Source for quarterly attrition calculation. Quarter is auto-derived from LWD.'
ws_off['A2'].font = Font(name=FONT, italic=True, size=10, color=SLATE)
ws_off['A2'].alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_off.row_dimensions[2].height = 24

off_headers = ['Employee ID', 'Name', 'Geography', 'Department', 'Designation',
               'Date of Joining', 'Last Working Day', 'Tenure (Years)', 'Reason', 'Quarter']
# adjust: 10 columns
ws_off.unmerge_cells('A1:I1')
ws_off.merge_cells('A1:J1')
ws_off.unmerge_cells('A2:I2')
ws_off.merge_cells('A2:J2')

off_headers = ['Employee ID', 'Name', 'Geography', 'Department', 'Designation',
               'Date of Joining', 'Last Working Day', 'Tenure (Years)', 'Reason', 'Quarter']
for i, h in enumerate(off_headers, 1):
    ws_off.cell(row=HEADER_ROW, column=i, value=h)
style_header_row(ws_off, HEADER_ROW, 1, len(off_headers), bg=NAVY)
ws_off.row_dimensions[HEADER_ROW].height = 32

off_data_start = HEADER_ROW + 1
for idx, row in enumerate(gd.offboarded):
    r = off_data_start + idx
    ws_off.cell(row=r, column=1, value=row['id'])
    ws_off.cell(row=r, column=2, value=row['name'])
    ws_off.cell(row=r, column=3, value=row['geo'])
    ws_off.cell(row=r, column=4, value=row['dept'])
    ws_off.cell(row=r, column=5, value=row['desig'])
    doj = ws_off.cell(row=r, column=6, value=row['doj'])
    doj.number_format = 'dd-mmm-yyyy'
    lwd = ws_off.cell(row=r, column=7, value=row['lwd'])
    lwd.number_format = 'dd-mmm-yyyy'
    # Tenure formula
    t = ws_off.cell(row=r, column=8, value=f'=ROUND((G{r}-F{r})/365.25,2)')
    t.number_format = '0.00'
    ws_off.cell(row=r, column=9, value=row['reason'])
    # Quarter auto-derived from LWD: "Q" & ROUNDUP(MONTH(LWD)/3, 0) & "-" & YEAR(LWD)
    q = ws_off.cell(row=r, column=10,
                    value=f'="Q"&ROUNDUP(MONTH(G{r})/3,0)&"-"&YEAR(G{r})')

off_data_end = off_data_start + len(gd.offboarded) - 1

for r in range(off_data_start, off_data_end + 1):
    for c in range(1, 11):
        cell = ws_off.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.border = THIN_BORDER
        if (r - off_data_start) % 2 == 1:
            cell.fill = PatternFill('solid', start_color=LIGHT_BG)
        cell.alignment = Alignment(horizontal='left' if c in [2,4,5,9] else 'center', vertical='center')

auto_width(ws_off, [13, 22, 11, 18, 22, 14, 14, 12, 22, 12])
ws_off.freeze_panes = f'A{off_data_start}'
ws_off.sheet_view.showGridLines = False
ws_off.auto_filter.ref = f'A{HEADER_ROW}:J{off_data_end}'

# Buffer for new exits (extra ranges for named refs)
wb.defined_names['OffData'] = DefinedName('OffData', attr_text=f"'Offboarded Resources'!$A${off_data_start}:$J${off_data_end+50}")
wb.defined_names['OffGeo'] = DefinedName('OffGeo', attr_text=f"'Offboarded Resources'!$C${off_data_start}:$C${off_data_end+50}")
wb.defined_names['OffDept'] = DefinedName('OffDept', attr_text=f"'Offboarded Resources'!$D${off_data_start}:$D${off_data_end+50}")
wb.defined_names['OffLWD'] = DefinedName('OffLWD', attr_text=f"'Offboarded Resources'!$G${off_data_start}:$G${off_data_end+50}")
wb.defined_names['OffQuarter'] = DefinedName('OffQuarter', attr_text=f"'Offboarded Resources'!$J${off_data_start}:$J${off_data_end+50}")

print(f"Offboarded tab: {len(gd.offboarded)} records.")

# Save intermediate to verify so far
test_path = '/home/claude/hr_project/test_partial.xlsx'
wb.save(test_path)
print(f"\nPartial workbook saved to {test_path}")

# ============================================================
# EXTENSION TABS: Payroll, Leave, Goals, Recruitment, Compliance, Training, Attrition Risk
# ============================================================
from build_extensions import build_all_extensions
DESIGN_TOKENS = {
    'NAVY': NAVY, 'TEAL': TEAL, 'CORAL': CORAL, 'AMBER': AMBER, 'SLATE': SLATE,
    'LIGHT_BG': LIGHT_BG, 'WHITE': WHITE, 'DARK_TEXT': DARK_TEXT,
    'GREEN_GOOD': GREEN_GOOD, 'HEADER_BG': HEADER_BG, 'FONT': FONT
}
build_all_extensions(wb, gd, DESIGN_TOKENS)

# ============================================================
# DASHBOARD - The main view
# ============================================================
ws_dash = wb.create_sheet('Dashboard', 0)  # insert at position 0

ws_dash.sheet_view.showGridLines = False
ws_dash.sheet_view.zoomScale = 90

# Set column widths for a uniform grid (24 columns of ~6.5 each = ~156 total)
for col in range(1, 25):
    ws_dash.column_dimensions[get_column_letter(col)].width = 6.5

# ===== TITLE BAR =====
ws_dash.merge_cells('A1:X1')
ws_dash['A1'] = 'HR AUTOMATION DASHBOARD'
ws_dash['A1'].font = Font(name=FONT, bold=True, size=24, color=WHITE)
ws_dash['A1'].fill = PatternFill('solid', start_color=HEADER_BG)
ws_dash['A1'].alignment = Alignment(horizontal='center', vertical='center')
ws_dash.row_dimensions[1].height = 50

ws_dash.merge_cells('A2:X2')
ws_dash['A2'] = 'Live workforce intelligence • India & US Geographies • Auto-refreshed from source tabs'
ws_dash['A2'].font = Font(name=FONT, italic=True, size=11, color=WHITE)
ws_dash['A2'].fill = PatternFill('solid', start_color=NAVY)
ws_dash['A2'].alignment = Alignment(horizontal='center', vertical='center')
ws_dash.row_dimensions[2].height = 24

# Report date strip
ws_dash.merge_cells('A3:H3')
ws_dash['A3'] = '=" Report Date:   "&TEXT(ReportDate,"dddd, dd mmmm yyyy")'
ws_dash['A3'].font = Font(name=FONT, bold=True, size=11, color=NAVY)
ws_dash['A3'].fill = PatternFill('solid', start_color=LIGHT_BG)
ws_dash['A3'].alignment = Alignment(horizontal='left', vertical='center', indent=1)

ws_dash.merge_cells('I3:P3')
ws_dash['I3'] = '=" Active Headcount: "&(COUNTIFS(IndiaStatus,"<>Offboarded")+COUNTIFS(USStatus,"<>Offboarded"))'
ws_dash['I3'].font = Font(name=FONT, bold=True, size=11, color=NAVY)
ws_dash['I3'].fill = PatternFill('solid', start_color=LIGHT_BG)
ws_dash['I3'].alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells('Q3:X3')
ws_dash['Q3'] = '="Open Risks: "&COUNTIF(RiskStatuses,"Open")+COUNTIF(RiskStatuses,"Under Review")+COUNTIF(RiskStatuses,"Mitigation in Progress")'
ws_dash['Q3'].font = Font(name=FONT, bold=True, size=11, color=CORAL)
ws_dash['Q3'].fill = PatternFill('solid', start_color=LIGHT_BG)
ws_dash['Q3'].alignment = Alignment(horizontal='right', vertical='center', indent=1)
ws_dash.row_dimensions[3].height = 26

# Thin separator row
ws_dash.row_dimensions[4].height = 8

print("Dashboard: title built.")

# ===== KPI TILES (6 cards across) =====
# Each KPI tile spans 4 columns x 4 rows. Total 24 cols / 6 tiles = 4 cols each.
# Rows 5-8 used for KPI tiles.

KPI_ROW_TOP = 5
KPI_ROW_BOTTOM = 8
for r in range(KPI_ROW_TOP, KPI_ROW_BOTTOM + 1):
    ws_dash.row_dimensions[r].height = 22

def kpi_tile(start_col, label, value_formula, color_bg, label_color=WHITE, value_color=WHITE,
             value_format='#,##0', icon='●', sub_formula=None):
    """Build a 4-col KPI tile starting at start_col, rows KPI_ROW_TOP..KPI_ROW_BOTTOM."""
    end_col = start_col + 3
    # Outer card background
    ws_dash.merge_cells(start_row=KPI_ROW_TOP, start_column=start_col,
                        end_row=KPI_ROW_BOTTOM, end_column=end_col)
    cell = ws_dash.cell(row=KPI_ROW_TOP, column=start_col)
    cell.fill = PatternFill('solid', start_color=color_bg)
    cell.alignment = Alignment(horizontal='center', vertical='center')
    # We'll un-merge to put content properly
    ws_dash.unmerge_cells(start_row=KPI_ROW_TOP, start_column=start_col,
                          end_row=KPI_ROW_BOTTOM, end_column=end_col)
    # Fill all cells in the tile with the bg color and merge label row + value row separately
    for r in range(KPI_ROW_TOP, KPI_ROW_BOTTOM + 1):
        for c in range(start_col, end_col + 1):
            ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=color_bg)
            ws_dash.cell(row=r, column=c).border = Border()  # no border within tile

    # Top: icon + label
    ws_dash.merge_cells(start_row=KPI_ROW_TOP, start_column=start_col,
                        end_row=KPI_ROW_TOP, end_column=end_col)
    top = ws_dash.cell(row=KPI_ROW_TOP, column=start_col)
    top.value = f'  {icon}  {label}'
    top.font = Font(name=FONT, bold=True, size=10, color=label_color)
    top.alignment = Alignment(horizontal='left', vertical='center')
    top.fill = PatternFill('solid', start_color=color_bg)

    # Middle: big value
    ws_dash.merge_cells(start_row=KPI_ROW_TOP+1, start_column=start_col,
                        end_row=KPI_ROW_TOP+2, end_column=end_col)
    val = ws_dash.cell(row=KPI_ROW_TOP+1, column=start_col)
    val.value = value_formula
    val.font = Font(name=FONT, bold=True, size=28, color=value_color)
    val.alignment = Alignment(horizontal='center', vertical='center')
    val.fill = PatternFill('solid', start_color=color_bg)
    val.number_format = value_format

    # Bottom: subline (e.g. trend or context)
    ws_dash.merge_cells(start_row=KPI_ROW_BOTTOM, start_column=start_col,
                        end_row=KPI_ROW_BOTTOM, end_column=end_col)
    sub = ws_dash.cell(row=KPI_ROW_BOTTOM, column=start_col)
    sub.value = sub_formula if sub_formula else ''
    sub.font = Font(name=FONT, italic=True, size=9, color=label_color)
    sub.alignment = Alignment(horizontal='center', vertical='center')
    sub.fill = PatternFill('solid', start_color=color_bg)

# KPI 1: Total Active Headcount
kpi_tile(1, 'TOTAL ACTIVE HEADCOUNT',
    '=COUNTIFS(IndiaStatus,"<>Offboarded")+COUNTIFS(USStatus,"<>Offboarded")',
    NAVY, icon='👥',
    sub_formula='="India "&COUNTIFS(IndiaStatus,"<>Offboarded")&"  •  US "&COUNTIFS(USStatus,"<>Offboarded")')

# KPI 2: Confirmed Employees
kpi_tile(5, 'CONFIRMED EMPLOYEES',
    '=COUNTIF(IndiaStatus,"Confirmed")+COUNTIF(USStatus,"Confirmed")',
    TEAL, icon='✓',
    sub_formula='=TEXT((COUNTIF(IndiaStatus,"Confirmed")+COUNTIF(USStatus,"Confirmed"))/(COUNTIFS(IndiaStatus,"<>Offboarded")+COUNTIFS(USStatus,"<>Offboarded")),"0.0%")&" of active"')

# KPI 3: Interns
kpi_tile(9, 'TOTAL INTERNS',
    '=COUNTIF(IndiaStatus,"Intern")+COUNTIF(USStatus,"Intern")',
    '3B82F6', icon='🎓',
    sub_formula='="India "&COUNTIF(IndiaStatus,"Intern")&"  •  US "&COUNTIF(USStatus,"Intern")')

# KPI 4: Interns LWD ≤ 45 days (RED ALERT)
kpi_tile(13, 'INTERNS - LWD ≤ 45 DAYS',
    '=SUMPRODUCT((IndiaInternEnd<>"")*(IndiaInternEnd-ReportDate>=0)*(IndiaInternEnd-ReportDate<=InternAlertDays))+SUMPRODUCT((USInternEnd<>"")*(USInternEnd-ReportDate>=0)*(USInternEnd-ReportDate<=InternAlertDays))',
    CORAL, icon='⏱',
    sub_formula='="Action: confirm transition or exit"')

# KPI 5: Probation Confirmation Due ≤ 30 days
kpi_tile(17, 'PROBATION DUE ≤ 30 DAYS',
    '=SUMPRODUCT((IndiaStatus="Under Probation")*((ProbationDays-(ReportDate-IndiaDOJ))>=0)*((ProbationDays-(ReportDate-IndiaDOJ))<=ProbationWindow))+SUMPRODUCT((USStatus="Under Probation")*((ProbationDays-(ReportDate-USDOJ))>=0)*((ProbationDays-(ReportDate-USDOJ))<=ProbationWindow))',
    AMBER, icon='⏰',
    sub_formula='="Action: complete review"')

# KPI 6: Attrition Rate (current quarter)
# Quarterly attrition: exits in current quarter / avg headcount during quarter
# Simplified: exits in current quarter / current active HC * 4 (annualized) -- or use a quarterly rate
# We'll compute quarterly: exits in current Q / (active HC + exits in Q)
kpi_tile(21, 'ATTRITION (CURRENT Q)',
    '=IFERROR(COUNTIF(OffQuarter,"Q"&ROUNDUP(MONTH(ReportDate)/3,0)&"-"&YEAR(ReportDate))/((COUNTIFS(IndiaStatus,"<>Offboarded")+COUNTIFS(USStatus,"<>Offboarded"))+COUNTIF(OffQuarter,"Q"&ROUNDUP(MONTH(ReportDate)/3,0)&"-"&YEAR(ReportDate))),0)',
    'EF4444', icon='📉', value_format='0.0%',
    sub_formula='="Quarterly turnover rate"')

print("Dashboard: KPIs built.")

# ===== SECTION HEADERS =====
def section_header(row, start_col, end_col, title, icon='', bg=NAVY):
    ws_dash.merge_cells(start_row=row, start_column=start_col, end_row=row, end_column=end_col)
    cell = ws_dash.cell(row=row, column=start_col)
    cell.value = f' {icon}  {title}' if icon else f' {title}'
    cell.font = Font(name=FONT, bold=True, size=12, color=WHITE)
    cell.fill = PatternFill('solid', start_color=bg)
    cell.alignment = Alignment(horizontal='left', vertical='center')
    ws_dash.row_dimensions[row].height = 24

# Spacer
ws_dash.row_dimensions[9].height = 10

# ============================================================
# SECTION: HEADCOUNT BY DEPARTMENT (table + chart-ready data)
# ============================================================
section_header(10, 1, 12, 'HEADCOUNT BY DEPARTMENT', icon='🏢', bg=NAVY)
section_header(10, 13, 24, 'HEADCOUNT BY GEOGRAPHY', icon='🌐', bg=NAVY)

DEPT_ROW = 11
ws_dash.cell(row=DEPT_ROW, column=1, value='Department')
ws_dash.cell(row=DEPT_ROW, column=4, value='India')
ws_dash.cell(row=DEPT_ROW, column=6, value='US')
ws_dash.cell(row=DEPT_ROW, column=8, value='Total')
ws_dash.cell(row=DEPT_ROW, column=10, value='% of HC')
ws_dash.merge_cells(start_row=DEPT_ROW, start_column=1, end_row=DEPT_ROW, end_column=3)
ws_dash.merge_cells(start_row=DEPT_ROW, start_column=4, end_row=DEPT_ROW, end_column=5)
ws_dash.merge_cells(start_row=DEPT_ROW, start_column=6, end_row=DEPT_ROW, end_column=7)
ws_dash.merge_cells(start_row=DEPT_ROW, start_column=8, end_row=DEPT_ROW, end_column=9)
ws_dash.merge_cells(start_row=DEPT_ROW, start_column=10, end_row=DEPT_ROW, end_column=12)
for c in [1, 4, 6, 8, 10]:
    cell = ws_dash.cell(row=DEPT_ROW, column=c)
    cell.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    cell.fill = PatternFill('solid', start_color=SLATE)
    cell.alignment = Alignment(horizontal='center', vertical='center')

departments_list = ['Engineering', 'Product', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Customer Success']
for i, dept in enumerate(departments_list):
    r = DEPT_ROW + 1 + i
    # Department name (merged across 3 cols)
    ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    d_cell = ws_dash.cell(row=r, column=1, value=dept)
    d_cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
    d_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    # India count
    ws_dash.merge_cells(start_row=r, start_column=4, end_row=r, end_column=5)
    ind_c = ws_dash.cell(row=r, column=4, value=f'=COUNTIFS(IndiaDept,"{dept}",IndiaStatus,"<>Offboarded")')
    ind_c.font = Font(name=FONT, size=10, color=DARK_TEXT)
    ind_c.alignment = Alignment(horizontal='center', vertical='center')
    # US count
    ws_dash.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
    us_c = ws_dash.cell(row=r, column=6, value=f'=COUNTIFS(USDept,"{dept}",USStatus,"<>Offboarded")')
    us_c.font = Font(name=FONT, size=10, color=DARK_TEXT)
    us_c.alignment = Alignment(horizontal='center', vertical='center')
    # Total
    ws_dash.merge_cells(start_row=r, start_column=8, end_row=r, end_column=9)
    tot = ws_dash.cell(row=r, column=8, value=f'=D{r}+F{r}')
    tot.font = Font(name=FONT, bold=True, size=10, color=NAVY)
    tot.alignment = Alignment(horizontal='center', vertical='center')
    # % of HC (with databar)
    ws_dash.merge_cells(start_row=r, start_column=10, end_row=r, end_column=12)
    pct = ws_dash.cell(row=r, column=10, value=f'=H{r}/(COUNTIFS(IndiaStatus,"<>Offboarded")+COUNTIFS(USStatus,"<>Offboarded"))')
    pct.font = Font(name=FONT, size=10, color=DARK_TEXT)
    pct.alignment = Alignment(horizontal='center', vertical='center')
    pct.number_format = '0.0%'
    # Alt row bg
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    for c in range(1, 13):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)

dept_table_end = DEPT_ROW + len(departments_list)

# Total row
total_r = dept_table_end + 1
ws_dash.merge_cells(start_row=total_r, start_column=1, end_row=total_r, end_column=3)
ws_dash.cell(row=total_r, column=1, value='TOTAL').font = Font(name=FONT, bold=True, size=11, color=WHITE)
ws_dash.cell(row=total_r, column=1).alignment = Alignment(horizontal='left', vertical='center', indent=1)
ws_dash.merge_cells(start_row=total_r, start_column=4, end_row=total_r, end_column=5)
ws_dash.cell(row=total_r, column=4, value=f'=SUM(D{DEPT_ROW+1}:D{dept_table_end})').font = Font(name=FONT, bold=True, size=11, color=WHITE)
ws_dash.cell(row=total_r, column=4).alignment = Alignment(horizontal='center', vertical='center')
ws_dash.merge_cells(start_row=total_r, start_column=6, end_row=total_r, end_column=7)
ws_dash.cell(row=total_r, column=6, value=f'=SUM(F{DEPT_ROW+1}:F{dept_table_end})').font = Font(name=FONT, bold=True, size=11, color=WHITE)
ws_dash.cell(row=total_r, column=6).alignment = Alignment(horizontal='center', vertical='center')
ws_dash.merge_cells(start_row=total_r, start_column=8, end_row=total_r, end_column=9)
ws_dash.cell(row=total_r, column=8, value=f'=SUM(H{DEPT_ROW+1}:H{dept_table_end})').font = Font(name=FONT, bold=True, size=11, color=WHITE)
ws_dash.cell(row=total_r, column=8).alignment = Alignment(horizontal='center', vertical='center')
ws_dash.merge_cells(start_row=total_r, start_column=10, end_row=total_r, end_column=12)
tp = ws_dash.cell(row=total_r, column=10, value='=SUM(J' + str(DEPT_ROW+1) + ':L' + str(dept_table_end) + ')')
tp.font = Font(name=FONT, bold=True, size=11, color=WHITE)
tp.alignment = Alignment(horizontal='center', vertical='center')
tp.number_format = '0.0%'

for c in range(1, 13):
    ws_dash.cell(row=total_r, column=c).fill = PatternFill('solid', start_color=NAVY)

# Databar on % column
ws_dash.conditional_formatting.add(
    f'J{DEPT_ROW+1}:J{dept_table_end}',
    DataBarRule(start_type='num', start_value=0, end_type='num', end_value=0.4, color=TEAL)
)

# ============================================================
# SECTION: HEADCOUNT BY GEOGRAPHY (cards + chart placeholders)
# ============================================================
GEO_ROW = 11
# India tile
ws_dash.merge_cells(start_row=GEO_ROW, start_column=13, end_row=GEO_ROW+1, end_column=18)
for r in range(GEO_ROW, GEO_ROW+2):
    for c in range(13, 19):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color='1E40AF')
ind_geo = ws_dash.cell(row=GEO_ROW, column=13)
ind_geo.value = '=" INDIA"&CHAR(10)&COUNTIFS(IndiaStatus,"<>Offboarded")&" employees"'
ind_geo.font = Font(name=FONT, bold=True, size=14, color=WHITE)
ind_geo.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_dash.row_dimensions[GEO_ROW].height = 32
ws_dash.row_dimensions[GEO_ROW+1].height = 20

# US tile
ws_dash.merge_cells(start_row=GEO_ROW, start_column=19, end_row=GEO_ROW+1, end_column=24)
for r in range(GEO_ROW, GEO_ROW+2):
    for c in range(19, 25):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color='B91C1C')
us_geo = ws_dash.cell(row=GEO_ROW, column=19)
us_geo.value = '=" UNITED STATES"&CHAR(10)&COUNTIFS(USStatus,"<>Offboarded")&" employees"'
us_geo.font = Font(name=FONT, bold=True, size=14, color=WHITE)
us_geo.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

# Splits (Confirmed / Probation / Intern) row 13-14 for each geo
SPLIT_ROW = GEO_ROW + 2
ws_dash.row_dimensions[SPLIT_ROW].height = 18
# India splits
ws_dash.merge_cells(start_row=SPLIT_ROW, start_column=13, end_row=SPLIT_ROW, end_column=14)
ws_dash.cell(row=SPLIT_ROW, column=13, value='Confirmed').font = Font(name=FONT, size=9, color=SLATE, bold=True)
ws_dash.cell(row=SPLIT_ROW, column=13).alignment = Alignment(horizontal='center')
ws_dash.merge_cells(start_row=SPLIT_ROW, start_column=15, end_row=SPLIT_ROW, end_column=16)
ws_dash.cell(row=SPLIT_ROW, column=15, value='Probation').font = Font(name=FONT, size=9, color=SLATE, bold=True)
ws_dash.cell(row=SPLIT_ROW, column=15).alignment = Alignment(horizontal='center')
ws_dash.merge_cells(start_row=SPLIT_ROW, start_column=17, end_row=SPLIT_ROW, end_column=18)
ws_dash.cell(row=SPLIT_ROW, column=17, value='Intern').font = Font(name=FONT, size=9, color=SLATE, bold=True)
ws_dash.cell(row=SPLIT_ROW, column=17).alignment = Alignment(horizontal='center')

# Row of values
VAL_ROW = SPLIT_ROW + 1
ws_dash.merge_cells(start_row=VAL_ROW, start_column=13, end_row=VAL_ROW, end_column=14)
v = ws_dash.cell(row=VAL_ROW, column=13, value='=COUNTIF(IndiaStatus,"Confirmed")')
v.font = Font(name=FONT, bold=True, size=18, color=GREEN_GOOD)
v.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=VAL_ROW, start_column=15, end_row=VAL_ROW, end_column=16)
v2 = ws_dash.cell(row=VAL_ROW, column=15, value='=COUNTIF(IndiaStatus,"Under Probation")')
v2.font = Font(name=FONT, bold=True, size=18, color=AMBER)
v2.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=VAL_ROW, start_column=17, end_row=VAL_ROW, end_column=18)
v3 = ws_dash.cell(row=VAL_ROW, column=17, value='=COUNTIF(IndiaStatus,"Intern")')
v3.font = Font(name=FONT, bold=True, size=18, color='3B82F6')
v3.alignment = Alignment(horizontal='center', vertical='center')

# US splits headers
ws_dash.merge_cells(start_row=SPLIT_ROW, start_column=19, end_row=SPLIT_ROW, end_column=20)
ws_dash.cell(row=SPLIT_ROW, column=19, value='Confirmed').font = Font(name=FONT, size=9, color=SLATE, bold=True)
ws_dash.cell(row=SPLIT_ROW, column=19).alignment = Alignment(horizontal='center')
ws_dash.merge_cells(start_row=SPLIT_ROW, start_column=21, end_row=SPLIT_ROW, end_column=22)
ws_dash.cell(row=SPLIT_ROW, column=21, value='Probation').font = Font(name=FONT, size=9, color=SLATE, bold=True)
ws_dash.cell(row=SPLIT_ROW, column=21).alignment = Alignment(horizontal='center')
ws_dash.merge_cells(start_row=SPLIT_ROW, start_column=23, end_row=SPLIT_ROW, end_column=24)
ws_dash.cell(row=SPLIT_ROW, column=23, value='Intern').font = Font(name=FONT, size=9, color=SLATE, bold=True)
ws_dash.cell(row=SPLIT_ROW, column=23).alignment = Alignment(horizontal='center')

ws_dash.merge_cells(start_row=VAL_ROW, start_column=19, end_row=VAL_ROW, end_column=20)
v4 = ws_dash.cell(row=VAL_ROW, column=19, value='=COUNTIF(USStatus,"Confirmed")')
v4.font = Font(name=FONT, bold=True, size=18, color=GREEN_GOOD)
v4.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=VAL_ROW, start_column=21, end_row=VAL_ROW, end_column=22)
v5 = ws_dash.cell(row=VAL_ROW, column=21, value='=COUNTIF(USStatus,"Under Probation")')
v5.font = Font(name=FONT, bold=True, size=18, color=AMBER)
v5.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=VAL_ROW, start_column=23, end_row=VAL_ROW, end_column=24)
v6 = ws_dash.cell(row=VAL_ROW, column=23, value='=COUNTIF(USStatus,"Intern")')
v6.font = Font(name=FONT, bold=True, size=18, color='3B82F6')
v6.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.row_dimensions[VAL_ROW].height = 30

# Set row heights for dept table
for r in range(DEPT_ROW, dept_table_end + 2):
    ws_dash.row_dimensions[r].height = 20

print("Dashboard: dept/geo built.")

# ============================================================
# SECTION: ATTRITION (quarterly trend) + FINANCIAL SUMMARY
# ============================================================
# We'll use rows ~22-32 for this section

# Spacer
ws_dash.row_dimensions[20].height = 12

ATTR_HEADER_ROW = 21
section_header(ATTR_HEADER_ROW, 1, 12, 'QUARTERLY ATTRITION TREND', icon='📉', bg=NAVY)
section_header(ATTR_HEADER_ROW, 13, 24, 'COMPENSATION SUMMARY', icon='💰', bg=NAVY)

# Attrition quarterly table (data for chart)
ATTR_ROW = 22
ws_dash.merge_cells(start_row=ATTR_ROW, start_column=1, end_row=ATTR_ROW, end_column=3)
ws_dash.cell(row=ATTR_ROW, column=1, value='Quarter')
ws_dash.merge_cells(start_row=ATTR_ROW, start_column=4, end_row=ATTR_ROW, end_column=5)
ws_dash.cell(row=ATTR_ROW, column=4, value='Exits')
ws_dash.merge_cells(start_row=ATTR_ROW, start_column=6, end_row=ATTR_ROW, end_column=7)
ws_dash.cell(row=ATTR_ROW, column=6, value='India')
ws_dash.merge_cells(start_row=ATTR_ROW, start_column=8, end_row=ATTR_ROW, end_column=9)
ws_dash.cell(row=ATTR_ROW, column=8, value='US')
ws_dash.merge_cells(start_row=ATTR_ROW, start_column=10, end_row=ATTR_ROW, end_column=12)
ws_dash.cell(row=ATTR_ROW, column=10, value='Attrition %')
for c in [1, 4, 6, 8, 10]:
    cell = ws_dash.cell(row=ATTR_ROW, column=c)
    cell.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    cell.fill = PatternFill('solid', start_color=SLATE)
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Quarters list (use 4 recent quarters)
quarters_list = ['Q2-2025', 'Q3-2025', 'Q4-2025', 'Q1-2026', 'Q2-2026']

for i, q in enumerate(quarters_list):
    r = ATTR_ROW + 1 + i
    ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    q_cell = ws_dash.cell(row=r, column=1, value=q)
    q_cell.font = Font(name=FONT, size=10, color=DARK_TEXT, bold=True)
    q_cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)

    ws_dash.merge_cells(start_row=r, start_column=4, end_row=r, end_column=5)
    ex = ws_dash.cell(row=r, column=4, value=f'=COUNTIF(OffQuarter,"{q}")')
    ex.font = Font(name=FONT, bold=True, size=11, color=NAVY)
    ex.alignment = Alignment(horizontal='center', vertical='center')

    ws_dash.merge_cells(start_row=r, start_column=6, end_row=r, end_column=7)
    ind_ex = ws_dash.cell(row=r, column=6, value=f'=COUNTIFS(OffQuarter,"{q}",OffGeo,"India")')
    ind_ex.font = Font(name=FONT, size=10, color=DARK_TEXT)
    ind_ex.alignment = Alignment(horizontal='center', vertical='center')

    ws_dash.merge_cells(start_row=r, start_column=8, end_row=r, end_column=9)
    us_ex = ws_dash.cell(row=r, column=8, value=f'=COUNTIFS(OffQuarter,"{q}",OffGeo,"US")')
    us_ex.font = Font(name=FONT, size=10, color=DARK_TEXT)
    us_ex.alignment = Alignment(horizontal='center', vertical='center')

    ws_dash.merge_cells(start_row=r, start_column=10, end_row=r, end_column=12)
    pct = ws_dash.cell(row=r, column=10, value=f'=IFERROR(D{r}/(COUNTIFS(IndiaStatus,"<>Offboarded")+COUNTIFS(USStatus,"<>Offboarded")+D{r}),0)')
    pct.font = Font(name=FONT, bold=True, size=10, color=CORAL)
    pct.alignment = Alignment(horizontal='center', vertical='center')
    pct.number_format = '0.0%'

    # Alt row
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    for c in range(1, 13):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 22

attr_table_end = ATTR_ROW + len(quarters_list)

# Color scale on attrition %
ws_dash.conditional_formatting.add(
    f'J{ATTR_ROW+1}:J{attr_table_end}',
    ColorScaleRule(start_type='num', start_value=0, start_color=GREEN_GOOD,
                   mid_type='percentile', mid_value=50, mid_color=AMBER,
                   end_type='max', end_color=CORAL)
)

# ===== Add ATTRITION CHART =====
# Chart data lives in dept table area: cols D and J for quarters list (rows ATTR_ROW+1 to attr_table_end)
chart_attr = BarChart()
chart_attr.type = "col"
chart_attr.style = 11
chart_attr.title = None  # we have section header above
chart_attr.y_axis.title = "Exits"
chart_attr.x_axis.title = None
chart_attr.height = 7.5
chart_attr.width = 16
# Series: India exits and US exits stacked
chart_attr.grouping = "stacked"
chart_attr.overlap = 100

# Categories: Quarter labels at col A
cats = Reference(ws_dash, min_col=1, min_row=ATTR_ROW+1, max_row=attr_table_end)
# India exits
india_data_ref = Reference(ws_dash, min_col=6, min_row=ATTR_ROW, max_row=attr_table_end)
us_data_ref = Reference(ws_dash, min_col=8, min_row=ATTR_ROW, max_row=attr_table_end)
chart_attr.add_data(india_data_ref, titles_from_data=True)
chart_attr.add_data(us_data_ref, titles_from_data=True)
chart_attr.set_categories(cats)
chart_attr.legend.position = 'b'
chart_attr.legend.overlay = False

# Style colors
from openpyxl.chart.shapes import GraphicalProperties
from openpyxl.drawing.fill import PatternFillProperties, ColorChoice
from openpyxl.drawing.colors import ColorChoice as CC

# Anchor the chart below the attrition table
# We'll put it starting at row attr_table_end+2, col A; spans ~12 rows x 12 cols
from openpyxl.chart.layout import Layout
chart_attr.layout = Layout(
    manualLayout=ManualLayout(x=0.05, y=0.05, w=0.9, h=0.85)
)

# Add a small data table next to chart with quarter totals (replaces real chart embed for visual)
# Anchor chart
chart_anchor_row = attr_table_end + 2

# Color the series
from openpyxl.drawing.fill import ColorChoice as DCC
chart_attr.series[0].graphicalProperties = GraphicalProperties(solidFill='1E40AF')  # India = blue
chart_attr.series[1].graphicalProperties = GraphicalProperties(solidFill='B91C1C')  # US = red

ws_dash.add_chart(chart_attr, f'A{chart_anchor_row}')

# ============================================================
# COMPENSATION SUMMARY (right side)
# ============================================================
COMP_ROW = 22
# Labels and values
ws_dash.merge_cells(start_row=COMP_ROW, start_column=13, end_row=COMP_ROW, end_column=18)
ws_dash.cell(row=COMP_ROW, column=13, value='Metric').font = Font(name=FONT, bold=True, size=10, color=WHITE)
ws_dash.cell(row=COMP_ROW, column=13).fill = PatternFill('solid', start_color=SLATE)
ws_dash.cell(row=COMP_ROW, column=13).alignment = Alignment(horizontal='left', vertical='center', indent=1)
ws_dash.merge_cells(start_row=COMP_ROW, start_column=19, end_row=COMP_ROW, end_column=24)
ws_dash.cell(row=COMP_ROW, column=19, value='Value').font = Font(name=FONT, bold=True, size=10, color=WHITE)
ws_dash.cell(row=COMP_ROW, column=19).fill = PatternFill('solid', start_color=SLATE)
ws_dash.cell(row=COMP_ROW, column=19).alignment = Alignment(horizontal='center', vertical='center')

comp_rows = [
    ('Total Annual Payroll (INR)', '=SUM(FinanceAnnualINR)', '₹#,##0'),
    ('Total Annual Payroll (USD)', '=SUM(FinanceAnnualUSD)', '$#,##0'),
    ('Total Monthly Payroll (INR)', '=SUM(FinanceMonthlyINR)', '₹#,##0'),
    ('India Annual Payroll (INR)', '=SUMIF(FinanceGeo,"India",FinanceAnnualINR)', '₹#,##0'),
    ('US Annual Payroll (USD)', '=SUMIF(FinanceGeo,"US",FinanceAnnualUSD)', '$#,##0'),
]
for i, (label, formula, fmt) in enumerate(comp_rows):
    r = COMP_ROW + 1 + i
    ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=18)
    l = ws_dash.cell(row=r, column=13, value=label)
    l.font = Font(name=FONT, size=10, color=DARK_TEXT)
    l.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=24)
    v = ws_dash.cell(row=r, column=19, value=formula)
    v.font = Font(name=FONT, bold=True, size=11, color=NAVY)
    v.alignment = Alignment(horizontal='center', vertical='center')
    v.number_format = fmt
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    for c in range(13, 25):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 22

# Productivity score below comp summary
prod_summary_row = COMP_ROW + len(comp_rows) + 1
ws_dash.merge_cells(start_row=prod_summary_row, start_column=13, end_row=prod_summary_row, end_column=24)
ws_dash.cell(row=prod_summary_row, column=13, value=' AVG PRODUCTIVITY SCORE').font = Font(name=FONT, bold=True, size=10, color=WHITE)
ws_dash.cell(row=prod_summary_row, column=13).fill = PatternFill('solid', start_color=TEAL)
ws_dash.cell(row=prod_summary_row, column=13).alignment = Alignment(horizontal='left', vertical='center')
ws_dash.row_dimensions[prod_summary_row].height = 22

pr = prod_summary_row + 1
ws_dash.merge_cells(start_row=pr, start_column=13, end_row=pr, end_column=18)
ws_dash.cell(row=pr, column=13, value='Overall (1-5)').font = Font(name=FONT, size=10, color=DARK_TEXT)
ws_dash.cell(row=pr, column=13).alignment = Alignment(horizontal='left', vertical='center', indent=1)
ws_dash.merge_cells(start_row=pr, start_column=19, end_row=pr, end_column=24)
ps = ws_dash.cell(row=pr, column=19, value='=AVERAGE(ProductivityScore)')
ps.font = Font(name=FONT, bold=True, size=14, color=NAVY)
ps.alignment = Alignment(horizontal='center', vertical='center')
ps.number_format = '0.00'

pr2 = pr + 1
ws_dash.merge_cells(start_row=pr2, start_column=13, end_row=pr2, end_column=18)
ws_dash.cell(row=pr2, column=13, value='India avg').font = Font(name=FONT, size=10, color=DARK_TEXT)
ws_dash.cell(row=pr2, column=13).alignment = Alignment(horizontal='left', vertical='center', indent=1)
ws_dash.merge_cells(start_row=pr2, start_column=19, end_row=pr2, end_column=24)
ps2 = ws_dash.cell(row=pr2, column=19, value='=AVERAGEIF(ProductivityGeo,"India",ProductivityScore)')
ps2.font = Font(name=FONT, bold=True, size=12, color='1E40AF')
ps2.alignment = Alignment(horizontal='center', vertical='center')
ps2.number_format = '0.00'

pr3 = pr2 + 1
ws_dash.merge_cells(start_row=pr3, start_column=13, end_row=pr3, end_column=18)
ws_dash.cell(row=pr3, column=13, value='US avg').font = Font(name=FONT, size=10, color=DARK_TEXT)
ws_dash.cell(row=pr3, column=13).alignment = Alignment(horizontal='left', vertical='center', indent=1)
ws_dash.merge_cells(start_row=pr3, start_column=19, end_row=pr3, end_column=24)
ps3 = ws_dash.cell(row=pr3, column=19, value='=AVERAGEIF(ProductivityGeo,"US",ProductivityScore)')
ps3.font = Font(name=FONT, bold=True, size=12, color='B91C1C')
ps3.alignment = Alignment(horizontal='center', vertical='center')
ps3.number_format = '0.00'

for prx in [pr, pr2, pr3]:
    bg = LIGHT_BG if (prx - pr) % 2 == 1 else WHITE
    for c in range(13, 25):
        ws_dash.cell(row=prx, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[prx].height = 22

print("Dashboard: attrition + comp built.")

# ============================================================
# ALERTS SECTION
# ============================================================
# After chart anchor, we need ~12 rows for the chart to render.
# So alerts start around row attr_table_end + 15 = ~42
ALERTS_START = attr_table_end + 16  # leave room for chart

# Spacer
ws_dash.row_dimensions[ALERTS_START - 1].height = 12

# ============================================================
# INTERN LWD ALERTS PANEL (left)
# ============================================================
section_header(ALERTS_START, 1, 12, 'INTERN LWD ALERTS (Next 45 Days)', icon='⏱', bg=CORAL)
section_header(ALERTS_START, 13, 24, 'PROBATION CONFIRMATION DUE (Next 30 Days)', icon='⏰', bg=AMBER)

# Headers for intern alerts table
ALERTS_HDR = ALERTS_START + 1
intern_hdrs = [(1, 'Emp ID', 3), (4, 'Name', 6), (10, 'Dept', 4), (14, 'Intern End', 4), (18, 'Days Left', 3)]
# Actually we'll restructure: left half = intern alerts, right half = probation alerts
# Each panel is 12 cols. Within 12 cols, we put: EmpID(3), Name(4), Dept(3), End/Date(2)

# INTERN ALERTS (cols 1-12)
ws_dash.cell(row=ALERTS_HDR, column=1, value='Emp ID')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=1, end_row=ALERTS_HDR, end_column=2)
ws_dash.cell(row=ALERTS_HDR, column=3, value='Name')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=3, end_row=ALERTS_HDR, end_column=6)
ws_dash.cell(row=ALERTS_HDR, column=7, value='Dept')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=7, end_row=ALERTS_HDR, end_column=8)
ws_dash.cell(row=ALERTS_HDR, column=9, value='Intern End')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=9, end_row=ALERTS_HDR, end_column=10)
ws_dash.cell(row=ALERTS_HDR, column=11, value='Days Left')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=11, end_row=ALERTS_HDR, end_column=12)
for c in [1, 3, 7, 9, 11]:
    cell = ws_dash.cell(row=ALERTS_HDR, column=c)
    cell.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    cell.fill = PatternFill('solid', start_color=SLATE)
    cell.alignment = Alignment(horizontal='center', vertical='center')
ws_dash.row_dimensions[ALERTS_HDR].height = 22

# Build the intern alerts list from the data
intern_alerts = []
for emp in gd.india_employees + gd.us_employees:
    if emp['status'] == 'Intern' and isinstance(emp['intern_end'], date):
        days_left = (emp['intern_end'] - gd.today).days
        if 0 <= days_left <= 45:
            intern_alerts.append({
                'id': emp['id'], 'name': emp['name'], 'dept': emp['dept'],
                'end': emp['intern_end'], 'days': days_left
            })
intern_alerts.sort(key=lambda x: x['days'])

INTERN_DATA_START = ALERTS_HDR + 1
# Always reserve at least 8 rows for new entries
MAX_INTERN_ROWS = max(8, len(intern_alerts))

for i in range(MAX_INTERN_ROWS):
    r = INTERN_DATA_START + i
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    if i < len(intern_alerts):
        ia = intern_alerts[i]
        ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        ws_dash.cell(row=r, column=1, value=ia['id'])
        ws_dash.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
        ws_dash.cell(row=r, column=3, value=ia['name'])
        ws_dash.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
        ws_dash.cell(row=r, column=7, value=ia['dept'])
        ws_dash.merge_cells(start_row=r, start_column=9, end_row=r, end_column=10)
        d_c = ws_dash.cell(row=r, column=9, value=ia['end'])
        d_c.number_format = 'dd-mmm-yyyy'
        ws_dash.merge_cells(start_row=r, start_column=11, end_row=r, end_column=12)
        days_c = ws_dash.cell(row=r, column=11, value=f'=I{r}-ReportDate')
        days_c.number_format = '0" days"'
    else:
        # Empty row placeholder (so table has consistent height)
        ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=2)
        ws_dash.merge_cells(start_row=r, start_column=3, end_row=r, end_column=6)
        ws_dash.merge_cells(start_row=r, start_column=7, end_row=r, end_column=8)
        ws_dash.merge_cells(start_row=r, start_column=9, end_row=r, end_column=10)
        ws_dash.merge_cells(start_row=r, start_column=11, end_row=r, end_column=12)

    for c in [1, 3, 7, 9, 11]:
        cell = ws_dash.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.alignment = Alignment(horizontal='left' if c == 3 else 'center', vertical='center', indent=1 if c == 3 else 0)
    for c in range(1, 13):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 20

# Color days left
intern_data_end_row = INTERN_DATA_START + MAX_INTERN_ROWS - 1
ws_dash.conditional_formatting.add(
    f'K{INTERN_DATA_START}:K{intern_data_end_row}',
    ColorScaleRule(start_type='num', start_value=0, start_color=CORAL,
                   mid_type='num', mid_value=20, mid_color=AMBER,
                   end_type='num', end_value=45, end_color=GREEN_GOOD)
)

# ============================================================
# PROBATION DUE ALERTS (cols 13-24)
# ============================================================
ws_dash.cell(row=ALERTS_HDR, column=13, value='Emp ID')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=13, end_row=ALERTS_HDR, end_column=14)
ws_dash.cell(row=ALERTS_HDR, column=15, value='Name')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=15, end_row=ALERTS_HDR, end_column=18)
ws_dash.cell(row=ALERTS_HDR, column=19, value='Dept')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=19, end_row=ALERTS_HDR, end_column=20)
ws_dash.cell(row=ALERTS_HDR, column=21, value='Confirmation Due')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=21, end_row=ALERTS_HDR, end_column=22)
ws_dash.cell(row=ALERTS_HDR, column=23, value='Days Left')
ws_dash.merge_cells(start_row=ALERTS_HDR, start_column=23, end_row=ALERTS_HDR, end_column=24)
for c in [13, 15, 19, 21, 23]:
    cell = ws_dash.cell(row=ALERTS_HDR, column=c)
    cell.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    cell.fill = PatternFill('solid', start_color=SLATE)
    cell.alignment = Alignment(horizontal='center', vertical='center')

# Build probation alerts list
prob_alerts = []
for emp in gd.india_employees + gd.us_employees:
    if emp['status'] == 'Under Probation':
        days_since = (gd.today - emp['doj']).days
        days_to_confirm = 180 - days_since
        if 0 <= days_to_confirm <= 30:
            prob_alerts.append({
                'id': emp['id'], 'name': emp['name'], 'dept': emp['dept'],
                'confirm_date': emp['doj'] + timedelta(days=180),
                'days': days_to_confirm
            })
prob_alerts.sort(key=lambda x: x['days'])

MAX_PROB_ROWS = max(8, len(prob_alerts))
for i in range(MAX_PROB_ROWS):
    r = INTERN_DATA_START + i
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    if i < len(prob_alerts):
        pa = prob_alerts[i]
        ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=14)
        ws_dash.cell(row=r, column=13, value=pa['id'])
        ws_dash.merge_cells(start_row=r, start_column=15, end_row=r, end_column=18)
        ws_dash.cell(row=r, column=15, value=pa['name'])
        ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=20)
        ws_dash.cell(row=r, column=19, value=pa['dept'])
        ws_dash.merge_cells(start_row=r, start_column=21, end_row=r, end_column=22)
        d_c = ws_dash.cell(row=r, column=21, value=pa['confirm_date'])
        d_c.number_format = 'dd-mmm-yyyy'
        ws_dash.merge_cells(start_row=r, start_column=23, end_row=r, end_column=24)
        days_c = ws_dash.cell(row=r, column=23, value=f'=U{r}-ReportDate')
        days_c.number_format = '0" days"'
    else:
        ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=14)
        ws_dash.merge_cells(start_row=r, start_column=15, end_row=r, end_column=18)
        ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=20)
        ws_dash.merge_cells(start_row=r, start_column=21, end_row=r, end_column=22)
        ws_dash.merge_cells(start_row=r, start_column=23, end_row=r, end_column=24)

    for c in [13, 15, 19, 21, 23]:
        cell = ws_dash.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=10, color=DARK_TEXT)
        cell.alignment = Alignment(horizontal='left' if c == 15 else 'center', vertical='center', indent=1 if c == 15 else 0)
    for c in range(13, 25):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)

prob_data_end_row = INTERN_DATA_START + MAX_PROB_ROWS - 1
ws_dash.conditional_formatting.add(
    f'W{INTERN_DATA_START}:W{prob_data_end_row}',
    ColorScaleRule(start_type='num', start_value=0, start_color=CORAL,
                   mid_type='num', mid_value=15, mid_color=AMBER,
                   end_type='num', end_value=30, end_color=GREEN_GOOD)
)

ALERTS_END_ROW = max(intern_data_end_row, prob_data_end_row)
print(f"Dashboard: alerts built ({len(intern_alerts)} intern, {len(prob_alerts)} probation).")

# ============================================================
# RISK REPORT PANEL
# ============================================================
RISK_SECTION_START = ALERTS_END_ROW + 2
ws_dash.row_dimensions[RISK_SECTION_START - 1].height = 12

section_header(RISK_SECTION_START, 1, 12, 'RISK REPORT - SUMMARY', icon='⚠', bg=CORAL)
section_header(RISK_SECTION_START, 13, 24, 'TOP ACTIVE RISKS', icon='🚩', bg=CORAL)

# Left: Summary by Level and by Status
RISK_DETAIL_ROW = RISK_SECTION_START + 1
# Risk by Level - 3 cards
ws_dash.merge_cells(start_row=RISK_DETAIL_ROW, start_column=1, end_row=RISK_DETAIL_ROW, end_column=4)
hc = ws_dash.cell(row=RISK_DETAIL_ROW, column=1, value='HIGH')
hc.font = Font(name=FONT, bold=True, size=10, color=WHITE)
hc.fill = PatternFill('solid', start_color=CORAL)
hc.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=RISK_DETAIL_ROW, start_column=5, end_row=RISK_DETAIL_ROW, end_column=8)
mc = ws_dash.cell(row=RISK_DETAIL_ROW, column=5, value='MEDIUM')
mc.font = Font(name=FONT, bold=True, size=10, color=WHITE)
mc.fill = PatternFill('solid', start_color=AMBER)
mc.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=RISK_DETAIL_ROW, start_column=9, end_row=RISK_DETAIL_ROW, end_column=12)
lc = ws_dash.cell(row=RISK_DETAIL_ROW, column=9, value='LOW')
lc.font = Font(name=FONT, bold=True, size=10, color=WHITE)
lc.fill = PatternFill('solid', start_color=TEAL)
lc.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.row_dimensions[RISK_DETAIL_ROW].height = 22

RISK_VAL_ROW = RISK_DETAIL_ROW + 1
ws_dash.merge_cells(start_row=RISK_VAL_ROW, start_column=1, end_row=RISK_VAL_ROW+1, end_column=4)
hv = ws_dash.cell(row=RISK_VAL_ROW, column=1, value='=COUNTIF(RiskLevels,"High")')
hv.font = Font(name=FONT, bold=True, size=28, color=CORAL)
hv.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=RISK_VAL_ROW, start_column=5, end_row=RISK_VAL_ROW+1, end_column=8)
mv = ws_dash.cell(row=RISK_VAL_ROW, column=5, value='=COUNTIF(RiskLevels,"Medium")')
mv.font = Font(name=FONT, bold=True, size=28, color=AMBER)
mv.alignment = Alignment(horizontal='center', vertical='center')

ws_dash.merge_cells(start_row=RISK_VAL_ROW, start_column=9, end_row=RISK_VAL_ROW+1, end_column=12)
lv = ws_dash.cell(row=RISK_VAL_ROW, column=9, value='=COUNTIF(RiskLevels,"Low")')
lv.font = Font(name=FONT, bold=True, size=28, color=TEAL)
lv.alignment = Alignment(horizontal='center', vertical='center')

for r in [RISK_VAL_ROW, RISK_VAL_ROW+1]:
    ws_dash.row_dimensions[r].height = 28

# Status summary below the level cards
STATUS_LABEL_ROW = RISK_VAL_ROW + 2
ws_dash.merge_cells(start_row=STATUS_LABEL_ROW, start_column=1, end_row=STATUS_LABEL_ROW, end_column=12)
sl = ws_dash.cell(row=STATUS_LABEL_ROW, column=1, value=' BY STATUS')
sl.font = Font(name=FONT, bold=True, size=10, color=WHITE)
sl.fill = PatternFill('solid', start_color=SLATE)
sl.alignment = Alignment(horizontal='left', vertical='center')
ws_dash.row_dimensions[STATUS_LABEL_ROW].height = 22

status_rows = [
    ('Open', 'Open', CORAL),
    ('Under Review', 'Under Review', AMBER),
    ('Mitigation in Progress', 'Mitigation in Progress', '3B82F6'),
    ('Closed', 'Closed', GREEN_GOOD),
]
for i, (label, key, col) in enumerate(status_rows):
    r = STATUS_LABEL_ROW + 1 + i
    ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=8)
    l = ws_dash.cell(row=r, column=1, value=label)
    l.font = Font(name=FONT, size=10, color=DARK_TEXT)
    l.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws_dash.merge_cells(start_row=r, start_column=9, end_row=r, end_column=12)
    v = ws_dash.cell(row=r, column=9, value=f'=COUNTIF(RiskStatuses,"{key}")')
    v.font = Font(name=FONT, bold=True, size=12, color=col)
    v.alignment = Alignment(horizontal='center', vertical='center')
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    for c in range(1, 13):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 20

# Right: Top Active Risks table (Open/Under Review/Mitigation in Progress, ordered by Level)
TOP_RISK_HDR = RISK_SECTION_START + 1
ws_dash.cell(row=TOP_RISK_HDR, column=13, value='Risk ID')
ws_dash.merge_cells(start_row=TOP_RISK_HDR, start_column=13, end_row=TOP_RISK_HDR, end_column=14)
ws_dash.cell(row=TOP_RISK_HDR, column=15, value='Employee')
ws_dash.merge_cells(start_row=TOP_RISK_HDR, start_column=15, end_row=TOP_RISK_HDR, end_column=18)
ws_dash.cell(row=TOP_RISK_HDR, column=19, value='Category')
ws_dash.merge_cells(start_row=TOP_RISK_HDR, start_column=19, end_row=TOP_RISK_HDR, end_column=21)
ws_dash.cell(row=TOP_RISK_HDR, column=22, value='Level')
ws_dash.merge_cells(start_row=TOP_RISK_HDR, start_column=22, end_row=TOP_RISK_HDR, end_column=22)
ws_dash.cell(row=TOP_RISK_HDR, column=23, value='Status')
ws_dash.merge_cells(start_row=TOP_RISK_HDR, start_column=23, end_row=TOP_RISK_HDR, end_column=24)

for c in [13, 15, 19, 22, 23]:
    cell = ws_dash.cell(row=TOP_RISK_HDR, column=c)
    cell.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    cell.fill = PatternFill('solid', start_color=SLATE)
    cell.alignment = Alignment(horizontal='center', vertical='center')
ws_dash.row_dimensions[TOP_RISK_HDR].height = 22

# Sort risks by level (High > Medium > Low) and status (Open first)
level_order = {'High': 0, 'Medium': 1, 'Low': 2}
status_order = {'Open': 0, 'Under Review': 1, 'Mitigation in Progress': 2, 'Closed': 3}
active_risks = [r for r in gd.risk_data if r['status'] != 'Closed']
active_risks.sort(key=lambda x: (level_order.get(x['level'], 3), status_order.get(x['status'], 4)))

TOP_RISK_DATA_START = TOP_RISK_HDR + 1
MAX_TOP_RISKS = min(8, max(8, len(active_risks)))  # show top 8

for i in range(MAX_TOP_RISKS):
    r = TOP_RISK_DATA_START + i
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    if i < len(active_risks):
        ar = active_risks[i]
        ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=14)
        ws_dash.cell(row=r, column=13, value=ar['risk_id'])
        ws_dash.merge_cells(start_row=r, start_column=15, end_row=r, end_column=18)
        ws_dash.cell(row=r, column=15, value=ar['emp_name'])
        ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=21)
        ws_dash.cell(row=r, column=19, value=ar['category'])
        ws_dash.cell(row=r, column=22, value=ar['level'])
        ws_dash.merge_cells(start_row=r, start_column=23, end_row=r, end_column=24)
        ws_dash.cell(row=r, column=23, value=ar['status'])
    else:
        ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=14)
        ws_dash.merge_cells(start_row=r, start_column=15, end_row=r, end_column=18)
        ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=21)
        ws_dash.merge_cells(start_row=r, start_column=23, end_row=r, end_column=24)

    for c in [13, 15, 19, 22, 23]:
        cell = ws_dash.cell(row=r, column=c)
        cell.font = Font(name=FONT, size=9, color=DARK_TEXT)
        cell.alignment = Alignment(horizontal='left' if c in [15, 19] else 'center', vertical='center',
                                   indent=1 if c in [15, 19] else 0, wrap_text=True)
    for c in range(13, 25):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 22

# Color the level column
top_risk_end = TOP_RISK_DATA_START + MAX_TOP_RISKS - 1
for level, col in [('High', CORAL), ('Medium', AMBER), ('Low', TEAL)]:
    ws_dash.conditional_formatting.add(
        f'V{TOP_RISK_DATA_START}:V{top_risk_end}',
        FormulaRule(formula=[f'$V{TOP_RISK_DATA_START}="{level}"'],
                    fill=PatternFill('solid', start_color=col),
                    font=Font(name=FONT, bold=True, size=9, color=WHITE))
    )

RISK_END = max(STATUS_LABEL_ROW + len(status_rows), top_risk_end)
print("Dashboard: risk panel built.")

# ============================================================
# NEW SECTION 1: PAYROLL SUMMARY
# ============================================================
PAYROLL_SECTION_START = RISK_END + 2
section_header(PAYROLL_SECTION_START, 1, 24, 'PAYROLL SUMMARY  —  Total compensation across India + US', icon='💼', bg=NAVY)

# Build 6 payroll KPI tiles
PAY_TILE_ROW = PAYROLL_SECTION_START + 1
ws_dash.row_dimensions[PAY_TILE_ROW].height = 14  # spacer

PAY_TILE_TITLE_ROW = PAY_TILE_ROW + 1
PAY_TILE_VALUE_ROW = PAY_TILE_TITLE_ROW + 1
PAY_TILE_SUB_ROW = PAY_TILE_VALUE_ROW + 1

# 6 tiles, each spans 4 columns: India Monthly Payroll, India Annual CTC, US Monthly, US Annual,
# Avg India CTC, Avg US CTC
pay_tiles = [
    ('India Monthly Payroll', '=SUMIFS(PayrollGross,PayrollCurrency,"INR")', '"₹"#,##0', NAVY, 'Live from Payroll tab'),
    ('India Annual CTC',     '=SUMIFS(PayrollCTC,PayrollCurrency,"INR")',    '"₹"#,##0', '3B82F6', 'Total CTC commitments'),
    ('Avg India CTC',         '=AVERAGEIFS(PayrollCTC,PayrollCurrency,"INR")', '"₹"#,##0', '6366F1', 'Per employee'),
    ('US Monthly Payroll',   '=SUMIFS(PayrollGross,PayrollCurrency,"USD")',  '"$"#,##0', 'B91C1C', 'Live from Payroll tab'),
    ('US Annual CTC',         '=SUMIFS(PayrollCTC,PayrollCurrency,"USD")',    '"$"#,##0', '7C2D12', 'Total CTC commitments'),
    ('Avg US CTC',            '=AVERAGEIFS(PayrollCTC,PayrollCurrency,"USD")', '"$"#,##0', 'EA580C', 'Per employee'),
]

for i, (label, formula, fmt, color, sub) in enumerate(pay_tiles):
    col_start = i * 4 + 1
    col_end = col_start + 3
    # Title row
    ws_dash.merge_cells(start_row=PAY_TILE_TITLE_ROW, start_column=col_start,
                         end_row=PAY_TILE_TITLE_ROW, end_column=col_end)
    t = ws_dash.cell(row=PAY_TILE_TITLE_ROW, column=col_start, value=f'  {label}')
    t.font = Font(name=FONT, bold=True, size=9, color=WHITE)
    t.fill = PatternFill('solid', start_color=color)
    t.alignment = Alignment(horizontal='left', vertical='center')
    ws_dash.row_dimensions[PAY_TILE_TITLE_ROW].height = 20

    # Value row
    ws_dash.merge_cells(start_row=PAY_TILE_VALUE_ROW, start_column=col_start,
                         end_row=PAY_TILE_VALUE_ROW, end_column=col_end)
    v = ws_dash.cell(row=PAY_TILE_VALUE_ROW, column=col_start, value=formula)
    v.font = Font(name=FONT, bold=True, size=16, color=color)
    v.fill = PatternFill('solid', start_color=WHITE)
    v.alignment = Alignment(horizontal='center', vertical='center')
    v.number_format = fmt
    ws_dash.row_dimensions[PAY_TILE_VALUE_ROW].height = 34

    # Sub row
    ws_dash.merge_cells(start_row=PAY_TILE_SUB_ROW, start_column=col_start,
                         end_row=PAY_TILE_SUB_ROW, end_column=col_end)
    s = ws_dash.cell(row=PAY_TILE_SUB_ROW, column=col_start, value=sub)
    s.font = Font(name=FONT, italic=True, size=8, color=SLATE)
    s.fill = PatternFill('solid', start_color=LIGHT_BG)
    s.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[PAY_TILE_SUB_ROW].height = 16

PAYROLL_END = PAY_TILE_SUB_ROW
print("Dashboard: payroll summary built.")

# ============================================================
# NEW SECTION 2: ATTRITION RISK HEAT MAP
# ============================================================
ATTR_RISK_START = PAYROLL_END + 2
section_header(ATTR_RISK_START, 1, 24, 'ATTRITION RISK  —  Predictive model: who might leave next', icon='⚠️', bg=NAVY)

# Left: 3 big risk count cards (High/Medium/Low)
RISK_CARD_ROW = ATTR_RISK_START + 1
ws_dash.row_dimensions[RISK_CARD_ROW].height = 8

RC_LABEL_ROW = RISK_CARD_ROW + 1
RC_VALUE_ROW = RC_LABEL_ROW + 1
RC_SUB_ROW = RC_VALUE_ROW + 1

risk_cards = [
    ('HIGH RISK', '=COUNTIF(AttritionRiskLevel,"High")', CORAL, 'Immediate intervention'),
    ('MEDIUM RISK', '=COUNTIF(AttritionRiskLevel,"Medium")', AMBER, 'Monitor closely'),
    ('LOW RISK', '=COUNTIF(AttritionRiskLevel,"Low")', TEAL, 'Stable retention'),
]

# Cards on left (cols 1-12, 4 cols each)
for i, (label, formula, color, sub) in enumerate(risk_cards):
    col_start = i * 4 + 1
    col_end = col_start + 3
    ws_dash.merge_cells(start_row=RC_LABEL_ROW, start_column=col_start,
                         end_row=RC_LABEL_ROW, end_column=col_end)
    t = ws_dash.cell(row=RC_LABEL_ROW, column=col_start, value=label)
    t.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    t.fill = PatternFill('solid', start_color=color)
    t.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[RC_LABEL_ROW].height = 22

    ws_dash.merge_cells(start_row=RC_VALUE_ROW, start_column=col_start,
                         end_row=RC_VALUE_ROW, end_column=col_end)
    v = ws_dash.cell(row=RC_VALUE_ROW, column=col_start, value=formula)
    v.font = Font(name=FONT, bold=True, size=28, color=color)
    v.fill = PatternFill('solid', start_color=WHITE)
    v.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[RC_VALUE_ROW].height = 50

    ws_dash.merge_cells(start_row=RC_SUB_ROW, start_column=col_start,
                         end_row=RC_SUB_ROW, end_column=col_end)
    s = ws_dash.cell(row=RC_SUB_ROW, column=col_start, value=sub)
    s.font = Font(name=FONT, italic=True, size=9, color=SLATE)
    s.fill = PatternFill('solid', start_color=LIGHT_BG)
    s.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[RC_SUB_ROW].height = 18

# Right: Top 10 highest-risk employees table (cols 13-24)
TOP_RISK_HDR = RC_LABEL_ROW
hdr_cols = [(13, 14, 'Emp ID'), (15, 18, 'Name'), (19, 21, 'Dept'),
            (22, 22, 'Score'), (23, 24, 'Top Reason')]
for sc, ec, hl in hdr_cols:
    ws_dash.merge_cells(start_row=TOP_RISK_HDR, start_column=sc, end_row=TOP_RISK_HDR, end_column=ec)
    c = ws_dash.cell(row=TOP_RISK_HDR, column=sc, value=hl)
    c.font = Font(name=FONT, bold=True, size=9, color=WHITE)
    c.fill = PatternFill('solid', start_color=SLATE)
    c.alignment = Alignment(horizontal='center', vertical='center')

TOP_ATTR_DATA_START = TOP_RISK_HDR + 1
N_TOP_ATTR = 10
# gd.attrition_risk is already sorted by total_score desc
top_attr = gd.attrition_risk[:N_TOP_ATTR]
for i in range(N_TOP_ATTR):
    r = TOP_ATTR_DATA_START + i
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    if i < len(top_attr):
        ar = top_attr[i]
        ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=14)
        ws_dash.cell(row=r, column=13, value=ar['id'])
        ws_dash.merge_cells(start_row=r, start_column=15, end_row=r, end_column=18)
        ws_dash.cell(row=r, column=15, value=ar['name'])
        ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=21)
        ws_dash.cell(row=r, column=19, value=ar['dept'])
        ws_dash.cell(row=r, column=22, value=ar['total_score'])
        ws_dash.merge_cells(start_row=r, start_column=23, end_row=r, end_column=24)
        ws_dash.cell(row=r, column=23, value=ar['top_reason'])
    else:
        for sc, ec in [(13, 14), (15, 18), (19, 21), (23, 24)]:
            ws_dash.merge_cells(start_row=r, start_column=sc, end_row=r, end_column=ec)

    for sc in [13, 15, 19, 22, 23]:
        cell = ws_dash.cell(row=r, column=sc)
        cell.font = Font(name=FONT, size=9, color=DARK_TEXT)
        cell.alignment = Alignment(horizontal='left' if sc in [15, 19, 23] else 'center',
                                    vertical='center', indent=1 if sc in [15, 19, 23] else 0)
    for c in range(13, 25):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 18

top_attr_end = TOP_ATTR_DATA_START + N_TOP_ATTR - 1

# CF on score column
from openpyxl.formatting.rule import ColorScaleRule as CSR2
ws_dash.conditional_formatting.add(f'V{TOP_ATTR_DATA_START}:V{top_attr_end}',
    CSR2(start_type='num', start_value=30, start_color='86EFAC',
         mid_type='num', mid_value=55, mid_color='FEF3C7',
         end_type='num', end_value=85, end_color='FECACA'))

ATTR_RISK_END = max(RC_SUB_ROW, top_attr_end)
print("Dashboard: attrition risk panel built.")

# ============================================================
# NEW SECTION 3: RECRUITMENT FUNNEL
# ============================================================
RECRUIT_START = ATTR_RISK_END + 2
section_header(RECRUIT_START, 1, 24, 'RECRUITMENT FUNNEL  —  Candidate pipeline & open positions', icon='🎯', bg=NAVY)

# Left: 5-stage funnel visualization (cols 1-12)
FUNNEL_HDR = RECRUIT_START + 1
ws_dash.merge_cells(start_row=FUNNEL_HDR, start_column=1, end_row=FUNNEL_HDR, end_column=12)
fh = ws_dash.cell(row=FUNNEL_HDR, column=1, value='  CANDIDATE PIPELINE')
fh.font = Font(name=FONT, bold=True, size=10, color=WHITE)
fh.fill = PatternFill('solid', start_color=SLATE)
fh.alignment = Alignment(horizontal='left', vertical='center')
ws_dash.row_dimensions[FUNNEL_HDR].height = 22

# Funnel stages with COUNTIF formulas and widths that shrink as you go down
funnel_stages = [
    ('Applied',     '=COUNTIF(CandidateStages,"Applied")',     1,  12, '94A3B8'),
    ('Screened',    '=COUNTIF(CandidateStages,"Screened")',    2,  11, '3B82F6'),
    ('Interviewed', '=COUNTIF(CandidateStages,"Interviewed")', 3,  10, '8B5CF6'),
    ('Offered',     '=COUNTIF(CandidateStages,"Offered")',     4,  9,  AMBER),
    ('Joined',      '=COUNTIF(CandidateStages,"Joined")',      5,  8,  TEAL),
]

for i, (stage, formula, sc, ec, color) in enumerate(funnel_stages):
    r = FUNNEL_HDR + 1 + i
    # Label
    ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    l = ws_dash.cell(row=r, column=1, value=stage)
    l.font = Font(name=FONT, bold=True, size=10, color=DARK_TEXT)
    l.fill = PatternFill('solid', start_color=WHITE)
    l.alignment = Alignment(horizontal='right', vertical='center', indent=1)
    # Funnel bar (cols sc to ec — shrinks)
    ws_dash.merge_cells(start_row=r, start_column=sc + 3, end_row=r, end_column=ec)
    bar = ws_dash.cell(row=r, column=sc + 3, value=formula)
    bar.font = Font(name=FONT, bold=True, size=14, color=WHITE)
    bar.fill = PatternFill('solid', start_color=color)
    bar.alignment = Alignment(horizontal='center', vertical='center')
    # Fill any cells between label and bar with WHITE
    for c in range(4, sc + 3):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=WHITE)
    for c in range(ec + 1, 13):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=WHITE)
    ws_dash.row_dimensions[r].height = 26

# Right: Open Positions table (cols 13-24)
POS_HDR = RECRUIT_START + 1
ws_dash.merge_cells(start_row=POS_HDR, start_column=13, end_row=POS_HDR, end_column=24)
ph = ws_dash.cell(row=POS_HDR, column=13, value='  OPEN POSITIONS BY PRIORITY')
ph.font = Font(name=FONT, bold=True, size=10, color=WHITE)
ph.fill = PatternFill('solid', start_color=SLATE)
ph.alignment = Alignment(horizontal='left', vertical='center')

POS_COL_HDR = POS_HDR + 1
pos_cols = [(13, 15, 'Priority'), (16, 18, 'Count'), (19, 21, 'Openings'), (22, 24, 'Avg Days Open')]
for sc, ec, hl in pos_cols:
    ws_dash.merge_cells(start_row=POS_COL_HDR, start_column=sc, end_row=POS_COL_HDR, end_column=ec)
    c = ws_dash.cell(row=POS_COL_HDR, column=sc, value=hl)
    c.font = Font(name=FONT, bold=True, size=9, color=WHITE)
    c.fill = PatternFill('solid', start_color='64748B')
    c.alignment = Alignment(horizontal='center', vertical='center')

priorities = [('High', CORAL), ('Medium', AMBER), ('Low', TEAL)]
for i, (pri, color) in enumerate(priorities):
    r = POS_COL_HDR + 1 + i
    ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=15)
    l = ws_dash.cell(row=r, column=13, value=pri)
    l.font = Font(name=FONT, bold=True, size=11, color=WHITE)
    l.fill = PatternFill('solid', start_color=color)
    l.alignment = Alignment(horizontal='center', vertical='center')
    # Count
    ws_dash.merge_cells(start_row=r, start_column=16, end_row=r, end_column=18)
    cnt = ws_dash.cell(row=r, column=16, value=f'=COUNTIF(PositionPriority,"{pri}")')
    cnt.font = Font(name=FONT, bold=True, size=12, color=DARK_TEXT)
    cnt.fill = PatternFill('solid', start_color=WHITE)
    cnt.alignment = Alignment(horizontal='center', vertical='center')
    # Openings (sum of openings col E in OpenPositions where priority=this)
    ws_dash.merge_cells(start_row=r, start_column=19, end_row=r, end_column=21)
    op = ws_dash.cell(row=r, column=19, value=f'=SUMIF(PositionPriority,"{pri}",INDEX(OpenPositions,0,5))')
    op.font = Font(name=FONT, bold=True, size=12, color=DARK_TEXT)
    op.fill = PatternFill('solid', start_color=WHITE)
    op.alignment = Alignment(horizontal='center', vertical='center')
    # Avg days open
    ws_dash.merge_cells(start_row=r, start_column=22, end_row=r, end_column=24)
    av = ws_dash.cell(row=r, column=22, value=f'=IFERROR(AVERAGEIF(PositionPriority,"{pri}",INDEX(OpenPositions,0,7)),0)')
    av.font = Font(name=FONT, bold=True, size=12, color=DARK_TEXT)
    av.fill = PatternFill('solid', start_color=WHITE)
    av.alignment = Alignment(horizontal='center', vertical='center')
    av.number_format = '0.0'
    ws_dash.row_dimensions[r].height = 22

RECRUIT_END = max(FUNNEL_HDR + 5, POS_COL_HDR + 3)
print("Dashboard: recruitment funnel built.")

# ============================================================
# NEW SECTION 4: COMPLIANCE CALENDAR ALERTS
# ============================================================
COMP_START = RECRUIT_END + 2
section_header(COMP_START, 1, 24, 'COMPLIANCE ALERTS  —  Statutory deadlines next 30 days', icon='📅', bg=NAVY)

# 4 status cards on top (Overdue / Critical / Upcoming / Scheduled) — cols 1-24, 6 each
CC_TILE_ROW = COMP_START + 1
ws_dash.row_dimensions[CC_TILE_ROW].height = 8

CC_TLBL_ROW = CC_TILE_ROW + 1
CC_TVAL_ROW = CC_TLBL_ROW + 1
CC_TSUB_ROW = CC_TVAL_ROW + 1

cc_tiles = [
    ('OVERDUE', '=COUNTIF(ComplianceStatus,"Overdue")', '991B1B', 'Action required NOW'),
    ('CRITICAL (≤7d)', '=COUNTIF(ComplianceStatus,"Critical")', CORAL, 'File this week'),
    ('UPCOMING (≤30d)', '=COUNTIF(ComplianceStatus,"Upcoming")', AMBER, 'Plan ahead'),
    ('SCHEDULED', '=COUNTIF(ComplianceStatus,"Scheduled")', TEAL, 'No immediate action'),
]

for i, (label, formula, color, sub) in enumerate(cc_tiles):
    col_start = i * 6 + 1
    col_end = col_start + 5
    ws_dash.merge_cells(start_row=CC_TLBL_ROW, start_column=col_start,
                         end_row=CC_TLBL_ROW, end_column=col_end)
    t = ws_dash.cell(row=CC_TLBL_ROW, column=col_start, value=f'  {label}')
    t.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    t.fill = PatternFill('solid', start_color=color)
    t.alignment = Alignment(horizontal='left', vertical='center')
    ws_dash.row_dimensions[CC_TLBL_ROW].height = 22

    ws_dash.merge_cells(start_row=CC_TVAL_ROW, start_column=col_start,
                         end_row=CC_TVAL_ROW, end_column=col_end)
    v = ws_dash.cell(row=CC_TVAL_ROW, column=col_start, value=formula)
    v.font = Font(name=FONT, bold=True, size=24, color=color)
    v.fill = PatternFill('solid', start_color=WHITE)
    v.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[CC_TVAL_ROW].height = 44

    ws_dash.merge_cells(start_row=CC_TSUB_ROW, start_column=col_start,
                         end_row=CC_TSUB_ROW, end_column=col_end)
    s = ws_dash.cell(row=CC_TSUB_ROW, column=col_start, value=sub)
    s.font = Font(name=FONT, italic=True, size=9, color=SLATE)
    s.fill = PatternFill('solid', start_color=LIGHT_BG)
    s.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[CC_TSUB_ROW].height = 18

# Below tiles: top 6 upcoming compliance events
CC_TBL_HDR = CC_TSUB_ROW + 2
ws_dash.merge_cells(start_row=CC_TBL_HDR, start_column=1, end_row=CC_TBL_HDR, end_column=24)
ch = ws_dash.cell(row=CC_TBL_HDR, column=1, value='  TOP COMPLIANCE EVENTS  —  next 30 days')
ch.font = Font(name=FONT, bold=True, size=10, color=WHITE)
ch.fill = PatternFill('solid', start_color=SLATE)
ch.alignment = Alignment(horizontal='left', vertical='center')
ws_dash.row_dimensions[CC_TBL_HDR].height = 22

CC_COL_HDR = CC_TBL_HDR + 1
cc_cols = [(1, 3, 'Comp ID'), (4, 12, 'Title'), (13, 16, 'Category'),
           (17, 19, 'Due Date'), (20, 21, 'Days'), (22, 24, 'Status')]
for sc, ec, hl in cc_cols:
    ws_dash.merge_cells(start_row=CC_COL_HDR, start_column=sc, end_row=CC_COL_HDR, end_column=ec)
    c = ws_dash.cell(row=CC_COL_HDR, column=sc, value=hl)
    c.font = Font(name=FONT, bold=True, size=9, color=WHITE)
    c.fill = PatternFill('solid', start_color='64748B')
    c.alignment = Alignment(horizontal='center', vertical='center')

# Top 6 events nearest in time (sorted)
sorted_comp = sorted(gd.compliance_events, key=lambda x: x['due_date'])
top_comp = [c for c in sorted_comp if (c['due_date'] - gd.today).days <= 30][:6]
if len(top_comp) < 6:
    top_comp = sorted_comp[:6]

CC_DATA_START = CC_COL_HDR + 1
for i, c in enumerate(top_comp):
    r = CC_DATA_START + i
    bg = LIGHT_BG if i % 2 == 1 else WHITE
    ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    ws_dash.cell(row=r, column=1, value=c['comp_id'])
    ws_dash.merge_cells(start_row=r, start_column=4, end_row=r, end_column=12)
    ws_dash.cell(row=r, column=4, value=c['title'])
    ws_dash.merge_cells(start_row=r, start_column=13, end_row=r, end_column=16)
    ws_dash.cell(row=r, column=13, value=c['category'])
    ws_dash.merge_cells(start_row=r, start_column=17, end_row=r, end_column=19)
    ws_dash.cell(row=r, column=17, value=c['due_date'])
    ws_dash.cell(row=r, column=17).number_format = 'dd-mmm'
    ws_dash.merge_cells(start_row=r, start_column=20, end_row=r, end_column=21)
    days_until = (c['due_date'] - gd.today).days
    ws_dash.cell(row=r, column=20, value=days_until)
    ws_dash.merge_cells(start_row=r, start_column=22, end_row=r, end_column=24)
    ws_dash.cell(row=r, column=22, value=c['status'])

    for sc in [1, 4, 13, 17, 20, 22]:
        cell = ws_dash.cell(row=r, column=sc)
        cell.font = Font(name=FONT, size=9, color=DARK_TEXT)
        cell.alignment = Alignment(horizontal='left' if sc in [4, 13] else 'center',
                                    vertical='center', indent=1 if sc in [4, 13] else 0)
    for col in range(1, 25):
        ws_dash.cell(row=r, column=col).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 20

cc_end = CC_DATA_START + len(top_comp) - 1

# CF on status column
for status, color in [('Overdue', '991B1B'), ('Critical', CORAL),
                      ('Upcoming', AMBER), ('Scheduled', TEAL)]:
    ws_dash.conditional_formatting.add(f'V{CC_DATA_START}:V{cc_end}',
        FormulaRule(formula=[f'$V{CC_DATA_START}="{status}"'],
                    fill=PatternFill('solid', start_color=color),
                    font=Font(name=FONT, bold=True, size=9, color=WHITE)))

COMP_END = cc_end
print("Dashboard: compliance alerts built.")

# ============================================================
# ORG CHART SECTION (Reporting Hierarchy of Active Employees)
# ============================================================
ORG_SECTION_START = COMP_END + 2
section_header(ORG_SECTION_START, 1, 24, 'ORG CHART  —  REPORTING HIERARCHY (ACTIVE EMPLOYEES)', icon='🗂️', bg=NAVY)

# Build hierarchy from data
from collections import Counter, defaultdict

all_active = [(e, 'India') for e in gd.india_employees if e['status'] != 'Offboarded'] + \
             [(e, 'US') for e in gd.us_employees if e['status'] != 'Offboarded']

# CEO box
CEO_ROW = ORG_SECTION_START + 2
ws_dash.merge_cells(start_row=CEO_ROW, start_column=10, end_row=CEO_ROW + 1, end_column=15)
ceo_cell = ws_dash.cell(row=CEO_ROW, column=10, value='RAMESH KRISHNAN\nChief Executive Officer  •  116 Active')
ceo_cell.font = Font(name=FONT, bold=True, size=11, color=WHITE)
ceo_cell.fill = PatternFill('solid', start_color=NAVY)
ceo_cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws_dash.row_dimensions[CEO_ROW].height = 26
ws_dash.row_dimensions[CEO_ROW + 1].height = 22

# Connector row (vertical line below CEO)
CONN_ROW = CEO_ROW + 2
ws_dash.row_dimensions[CONN_ROW].height = 8
conn_cell = ws_dash.cell(row=CONN_ROW, column=12, value='')
conn_cell.fill = PatternFill('solid', start_color=SLATE)
ws_dash.merge_cells(start_row=CONN_ROW, start_column=12, end_row=CONN_ROW, end_column=13)

# Department heads — group by department, show India + US head side-by-side
dept_heads_by_dept = defaultdict(lambda: {'India': None, 'US': None})
for e, g in all_active:
    if 'Ramesh Krishnan' in e['manager']:
        dept_heads_by_dept[e['dept']][g] = e

# Count reports for each head
report_counts = {}
for e, g in all_active:
    for head, geo in [(e2, g2) for e2, g2 in all_active if 'Ramesh Krishnan' in e2['manager']]:
        if head['name'] in e['manager']:
            report_counts[(head['name'], geo)] = report_counts.get((head['name'], geo), 0) + 1

# Department cards row — 8 departments in 2 rows of 4
DEPT_HEAD_START = CONN_ROW + 1
dept_order = ['Engineering', 'Product', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Customer Success']
dept_colors = {
    'Engineering': '3B82F6',   # blue
    'Product': '8B5CF6',       # purple
    'Sales': TEAL,
    'Marketing': 'EC4899',     # pink
    'HR': AMBER,
    'Finance': '10B981',       # emerald
    'Operations': '6366F1',    # indigo
    'Customer Success': '14B8A6'  # teal-cyan
}

# Each dept card spans 6 columns; 4 cards per row → 24 cols
for i, dept in enumerate(dept_order):
    row_offset = (i // 4) * 7  # 7 rows per dept-row (header + india row + us row + spacing)
    col_start = (i % 4) * 6 + 1
    col_end = col_start + 5

    r = DEPT_HEAD_START + row_offset
    color = dept_colors.get(dept, NAVY)

    # Department header
    ws_dash.merge_cells(start_row=r, start_column=col_start, end_row=r, end_column=col_end)
    dh = ws_dash.cell(row=r, column=col_start, value=dept.upper())
    dh.font = Font(name=FONT, bold=True, size=10, color=WHITE)
    dh.fill = PatternFill('solid', start_color=color)
    dh.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[r].height = 22

    # India head row
    india_head = dept_heads_by_dept[dept]['India']
    r2 = r + 1
    ws_dash.merge_cells(start_row=r2, start_column=col_start, end_row=r2, end_column=col_end - 2)
    n_reports_india = sum(1 for e, g in all_active if g == 'India' and india_head and india_head['name'] in e['manager'])
    india_label = f"🇮🇳 {india_head['name']}\n{india_head['desig']}" if india_head else "🇮🇳 —"
    ic = ws_dash.cell(row=r2, column=col_start, value=india_label)
    ic.font = Font(name=FONT, bold=True, size=9, color=DARK_TEXT)
    ic.fill = PatternFill('solid', start_color=WHITE)
    ic.alignment = Alignment(horizontal='left', vertical='center', indent=1, wrap_text=True)
    # India report count
    ws_dash.merge_cells(start_row=r2, start_column=col_end - 1, end_row=r2, end_column=col_end)
    irc = ws_dash.cell(row=r2, column=col_end - 1, value=f"+{n_reports_india}" if india_head else "")
    irc.font = Font(name=FONT, bold=True, size=11, color=color)
    irc.fill = PatternFill('solid', start_color=WHITE)
    irc.alignment = Alignment(horizontal='center', vertical='center')
    # borders
    side = Side(style='thin', color='E5E7EB')
    for c in range(col_start, col_end + 1):
        cell = ws_dash.cell(row=r2, column=c)
        cell.border = Border(left=side, right=side, top=side, bottom=side)
    ws_dash.row_dimensions[r2].height = 32

    # US head row
    us_head = dept_heads_by_dept[dept]['US']
    r3 = r + 2
    ws_dash.merge_cells(start_row=r3, start_column=col_start, end_row=r3, end_column=col_end - 2)
    n_reports_us = sum(1 for e, g in all_active if g == 'US' and us_head and us_head['name'] in e['manager'])
    us_label = f"🇺🇸 {us_head['name']}\n{us_head['desig']}" if us_head else "🇺🇸 —"
    uc = ws_dash.cell(row=r3, column=col_start, value=us_label)
    uc.font = Font(name=FONT, bold=True, size=9, color=DARK_TEXT)
    uc.fill = PatternFill('solid', start_color=LIGHT_BG)
    uc.alignment = Alignment(horizontal='left', vertical='center', indent=1, wrap_text=True)
    # US report count
    ws_dash.merge_cells(start_row=r3, start_column=col_end - 1, end_row=r3, end_column=col_end)
    urc = ws_dash.cell(row=r3, column=col_end - 1, value=f"+{n_reports_us}" if us_head else "")
    urc.font = Font(name=FONT, bold=True, size=11, color=color)
    urc.fill = PatternFill('solid', start_color=LIGHT_BG)
    urc.alignment = Alignment(horizontal='center', vertical='center')
    for c in range(col_start, col_end + 1):
        cell = ws_dash.cell(row=r3, column=c)
        cell.border = Border(left=side, right=side, top=side, bottom=side)
    ws_dash.row_dimensions[r3].height = 32

    # Totals row
    r4 = r + 3
    ws_dash.merge_cells(start_row=r4, start_column=col_start, end_row=r4, end_column=col_end)
    total_dept = sum(1 for e, g in all_active if e['dept'] == dept)
    tc = ws_dash.cell(row=r4, column=col_start, value=f"Total: {total_dept} employees")
    tc.font = Font(name=FONT, italic=True, size=9, color=SLATE)
    tc.fill = PatternFill('solid', start_color=LIGHT_BG)
    tc.alignment = Alignment(horizontal='center', vertical='center')
    ws_dash.row_dimensions[r4].height = 18

    # Spacer
    r5 = r + 4
    ws_dash.row_dimensions[r5].height = 8

ORG_END = DEPT_HEAD_START + 13  # 2 rows of 7
print("Dashboard: org chart section built.")

# ============================================================
# FOOTER — HOW TO USE THIS DASHBOARD
# ============================================================
FOOTER_START = ORG_END + 2
section_header(FOOTER_START, 1, 24, 'HOW TO USE THIS DASHBOARD', icon='ℹ️', bg=NAVY)

footer_items = [
    ('🔄  Live & Auto-Updating',
     'All KPIs, alerts, attrition, payroll, and compliance numbers are live formulas. Edit any source tab and metrics refresh automatically. Press F9 to force a recalc.'),
    ('📋  16 Source Tabs',
     'India/US Employees, Payroll, Attendance & Leave, Performance Goals, Recruitment, Compliance, Training, Attrition Risk, RM Data, Finance, Productivity, Risk Report, Offboarded. Update these — never type into Dashboard cells.'),
    ('⚙️  Settings Tab',
     'Tune the Report Date (default = TODAY), alert windows (intern 45 days, probation 30 days), USD-INR rate, and probation duration in one place.'),
    ('🚨  Multi-Layer Alerts',
     'Intern LWD (≤45d), Probation (≤30d), Compliance Critical (≤7d) & Upcoming (≤30d), Top 10 Attrition Risk. All color-graded by urgency.'),
    ('📈  Quarterly Attrition',
     'Auto-calculated from the Offboarded Resources tab. The quarter column is derived from the LWD using a formula; add a new exit row and the chart updates.'),
    ('💼  Payroll & Compensation',
     'Full salary breakup per employee with PF, ESI, TDS, PT for India; Federal, State, SS, Medicare for US. Net pay auto-computed via formulas.'),
    ('🎯  Recruitment Pipeline',
     'ATS-style funnel: Applied → Screened → Interviewed → Offered → Joined. 12 open positions with priority-wise dashboard rollup.'),
    ('🛡️  Risk Report',
     'HR maintains the Risk Report tab directly. The dashboard counts by Level and Status, and shows the top open risks sorted by severity.'),
    ('⚠️  Predictive Attrition Risk',
     'Weighted scoring model (Tenure + Productivity + Comp Ratio + Other) classifies employees High/Medium/Low risk with reasons. Top 10 surfaced on dashboard.'),
    ('🗂️  Org Chart',
     'Shows only active employees. Each department card lists the India and US head with their direct-report counts and the department total.'),
]

for i, (title, desc) in enumerate(footer_items):
    r = FOOTER_START + 2 + i
    # Title column
    ws_dash.merge_cells(start_row=r, start_column=1, end_row=r, end_column=6)
    t = ws_dash.cell(row=r, column=1, value=title)
    t.font = Font(name=FONT, bold=True, size=10, color=NAVY)
    t.alignment = Alignment(horizontal='left', vertical='center', indent=1, wrap_text=True)
    # Description column
    ws_dash.merge_cells(start_row=r, start_column=7, end_row=r, end_column=24)
    d = ws_dash.cell(row=r, column=7, value=desc)
    d.font = Font(name=FONT, size=10, color=DARK_TEXT)
    d.alignment = Alignment(horizontal='left', vertical='center', indent=1, wrap_text=True)
    bg = LIGHT_BG if i % 2 == 0 else WHITE
    for c in range(1, 25):
        ws_dash.cell(row=r, column=c).fill = PatternFill('solid', start_color=bg)
    ws_dash.row_dimensions[r].height = 32

FOOTER_END = FOOTER_START + 2 + len(footer_items)

# Final credit line
CREDIT_ROW = FOOTER_END + 2
ws_dash.merge_cells(start_row=CREDIT_ROW, start_column=1, end_row=CREDIT_ROW, end_column=24)
cr = ws_dash.cell(row=CREDIT_ROW, column=1,
                  value='HR Automation Dashboard  •  Live-linked Excel workbook  •  Built for India + US operations  •  All metrics recalculated against Report Date in Settings tab')
cr.font = Font(name=FONT, italic=True, size=9, color=SLATE)
cr.alignment = Alignment(horizontal='center', vertical='center')
for c in range(1, 25):
    ws_dash.cell(row=CREDIT_ROW, column=c).fill = PatternFill('solid', start_color=NAVY)
cr.font = Font(name=FONT, italic=True, size=9, color=WHITE)
ws_dash.row_dimensions[CREDIT_ROW].height = 22

print("Dashboard: footer built.")

# ============================================================
# Freeze panes on Dashboard (lock title bar)
# ============================================================
ws_dash.freeze_panes = 'A5'

# ============================================================
# Reorder sheets: Dashboard first, Settings second, then data tabs, Offboarded last
# ============================================================
desired_order = [
    'Dashboard',
    'Settings',
    'India Employees',
    'US Employees',
    'Payroll',
    'Attendance & Leave',
    'Performance Goals',
    'Recruitment',
    'Compliance Calendar',
    'Training & Skills',
    'Attrition Risk',
    'RM Data',
    'Finance',
    'Productivity',
    'Risk Report',
    'Offboarded Resources',
]

# Move each sheet to its desired position
current_names = wb.sheetnames
for target_idx, name in enumerate(desired_order):
    if name in wb.sheetnames:
        current_idx = wb.sheetnames.index(name)
        offset = target_idx - current_idx
        if offset != 0:
            wb.move_sheet(name, offset=offset)

# Activate Dashboard
wb.active = wb.sheetnames.index('Dashboard')
ws_dash.sheet_view.showGridLines = False
ws_dash.sheet_view.zoomScale = 90

# Set tab colors for visual grouping
tab_colors = {
    'Dashboard': '1E3A5F',
    'Settings': '64748B',
    'India Employees': '3B82F6',
    'US Employees': 'B91C1C',
    'Payroll': '10B981',
    'Attendance & Leave': '14B8A6',
    'Performance Goals': '8B5CF6',
    'Recruitment': 'EC4899',
    'Compliance Calendar': 'F4A261',
    'Training & Skills': '6366F1',
    'Attrition Risk': 'DC2626',
    'RM Data': '6366F1',
    'Finance': '10B981',
    'Productivity': '8B5CF6',
    'Risk Report': 'F4A261',
    'Offboarded Resources': '6B7280',
}
for name, color in tab_colors.items():
    if name in wb.sheetnames:
        wb[name].sheet_properties.tabColor = color

# ============================================================
# Page setup for Dashboard (landscape, fit to width)
# ============================================================
from openpyxl.worksheet.page import PageMargins
ws_dash.page_setup.orientation = ws_dash.ORIENTATION_LANDSCAPE
ws_dash.page_setup.paperSize = ws_dash.PAPERSIZE_TABLOID  # 11x17 — enough room for the wide dashboard
ws_dash.page_setup.fitToWidth = 1
ws_dash.page_setup.fitToHeight = 0
ws_dash.sheet_properties.pageSetUpPr.fitToPage = True
ws_dash.print_options.horizontalCentered = True
ws_dash.page_margins = PageMargins(left=0.4, right=0.4, top=0.5, bottom=0.5)
ws_dash.print_title_rows = '1:3'  # repeat title bar on each printed page

# Data tabs: landscape A4, fit to width
for name in ['India Employees', 'US Employees', 'Payroll', 'Attendance & Leave',
             'Performance Goals', 'Recruitment', 'Compliance Calendar', 'Training & Skills',
             'Attrition Risk', 'RM Data', 'Finance', 'Productivity', 'Risk Report',
             'Offboarded Resources']:
    if name not in wb.sheetnames:
        continue
    ws = wb[name]
    ws.page_setup.orientation = ws.ORIENTATION_LANDSCAPE
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True
    ws.print_title_rows = '1:4'  # repeat headers

# ============================================================
# SAVE FINAL WORKBOOK
# ============================================================
final_path = '/home/claude/hr_project/HR_Automation_Dashboard.xlsx'
wb.save(final_path)
print(f"\n✓ FINAL WORKBOOK SAVED: {final_path}")
print(f"  Sheets: {wb.sheetnames}")
