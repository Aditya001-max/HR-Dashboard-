"""
Extension tabs for HR Automation Dashboard:
- Payroll
- Attendance & Leave
- Performance Goals
- Recruitment Pipeline
- Compliance Calendar
- Training & Development

This module is imported by build_workbook.py and operates on the shared `wb` workbook.
All functions take (wb, gd, design_tokens) and add a sheet.
"""

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.formatting.rule import (
    CellIsRule, FormulaRule, ColorScaleRule, DataBarRule
)
from openpyxl.worksheet.datavalidation import DataValidation


def build_payroll_tab(wb, gd, T):
    """T = design tokens dict with NAVY, TEAL, CORAL, etc."""
    ws = wb.create_sheet('Payroll')
    HEADER_ROW = 4

    # Title bar rows 1-3
    ws.merge_cells('A1:O1')
    title = ws['A1']
    title.value = 'PAYROLL  —  Salary breakup, statutory deductions & net pay'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:O2')
    sub = ws['A2']
    sub.value = '   India: Basic 40% + HRA 20% + Special, with PF/ESI/PT/TDS  •  US: Federal + State + SS + Medicare'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    headers = ['Emp ID', 'Name', 'Geo', 'Dept', 'CTC (Annual)', 'Basic', 'HRA / Allow', 'Special',
               'Gross', 'PF / Fed Tax', 'ESI / SS', 'PT / Medicare', 'TDS / State', 'Net Pay', 'Currency']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=HEADER_ROW, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=10, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['NAVY'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[HEADER_ROW].height = 32

    data_start = HEADER_ROW + 1
    for i, p in enumerate(gd.payroll_data):
        r = data_start + i
        ws.cell(row=r, column=1, value=p['id'])
        ws.cell(row=r, column=2, value=p['name'])
        ws.cell(row=r, column=3, value=p['geo'])
        ws.cell(row=r, column=4, value=p['dept'])
        ws.cell(row=r, column=5, value=p['ctc'])
        ws.cell(row=r, column=6, value=p['basic'])
        ws.cell(row=r, column=7, value=p['hra'])
        ws.cell(row=r, column=8, value=p['special'])
        # Gross as formula = Basic + HRA + Special (so it auto-recalcs if user edits)
        ws.cell(row=r, column=9, value=f'=F{r}+G{r}+H{r}')
        ws.cell(row=r, column=10, value=p['pf_emp'])
        ws.cell(row=r, column=11, value=p['esi'])
        ws.cell(row=r, column=12, value=p['pt'])
        ws.cell(row=r, column=13, value=p['tds'])
        # Net = Gross - all deductions (formula)
        ws.cell(row=r, column=14, value=f'=I{r}-J{r}-K{r}-L{r}-M{r}')
        ws.cell(row=r, column=15, value=p['currency'])

        # Number format - currency columns
        for col in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
            cell = ws.cell(row=r, column=col)
            if p['currency'] == 'INR':
                cell.number_format = '₹#,##0'
            else:
                cell.number_format = '$#,##0'
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='right', vertical='center')

        for col in [1, 2, 3, 4, 15]:
            cell = ws.cell(row=r, column=col)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [2, 4] else 'center',
                                         vertical='center', indent=1 if col in [2, 4] else 0)

        # Alternating row colors
        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 16):
            ws.cell(row=r, column=col).fill = PatternFill('solid', start_color=bg)

    data_end = data_start + len(gd.payroll_data) - 1

    # Totals row
    total_row = data_end + 1
    ws.cell(row=total_row, column=1, value='TOTAL')
    ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=4)
    for col in [5, 6, 7, 8, 9, 10, 11, 12, 13, 14]:
        # Only sum same-currency rows? For mixed currencies this is conceptual — show India totals
        col_letter = chr(64 + col)
        ws.cell(row=total_row, column=col,
                value=f'=SUMIFS({col_letter}{data_start}:{col_letter}{data_end},$O${data_start}:$O${data_end},"INR")')
        ws.cell(row=total_row, column=col).number_format = '₹#,##0'
    for col in range(1, 16):
        cell = ws.cell(row=total_row, column=col)
        cell.font = Font(name=T['FONT'], bold=True, size=10, color=T['WHITE'])
        cell.fill = PatternFill('solid', start_color=T['NAVY'])
        cell.alignment = Alignment(horizontal='center' if col > 4 else 'left',
                                     vertical='center', indent=1 if col == 1 else 0)
    ws.row_dimensions[total_row].height = 22

    # Column widths
    widths = [10, 22, 8, 16, 14, 12, 12, 12, 12, 13, 11, 13, 12, 13, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # Conditional formatting - color scale on Net Pay column (within currency groups it'll look weird, but it's directional)
    ws.conditional_formatting.add(f'N{data_start}:N{data_end}',
        ColorScaleRule(start_type='min', start_color='FECACA',
                       mid_type='percentile', mid_value=50, mid_color='FEF3C7',
                       end_type='max', end_color='86EFAC'))

    # Freeze panes
    ws.freeze_panes = 'C5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['PayrollData'] = DefinedName('PayrollData',
        attr_text=f"'Payroll'!$A${data_start}:$O${data_end}")
    wb.defined_names['PayrollGeo'] = DefinedName('PayrollGeo',
        attr_text=f"'Payroll'!$C${data_start}:$C${data_end}")
    wb.defined_names['PayrollDept'] = DefinedName('PayrollDept',
        attr_text=f"'Payroll'!$D${data_start}:$D${data_end}")
    wb.defined_names['PayrollGross'] = DefinedName('PayrollGross',
        attr_text=f"'Payroll'!$I${data_start}:$I${data_end}")
    wb.defined_names['PayrollNet'] = DefinedName('PayrollNet',
        attr_text=f"'Payroll'!$N${data_start}:$N${data_end}")
    wb.defined_names['PayrollCurrency'] = DefinedName('PayrollCurrency',
        attr_text=f"'Payroll'!$O${data_start}:$O${data_end}")
    wb.defined_names['PayrollCTC'] = DefinedName('PayrollCTC',
        attr_text=f"'Payroll'!$E${data_start}:$E${data_end}")

    print(f"  Payroll tab: {len(gd.payroll_data)} records (₹INR + $USD).")
    return data_start, data_end


def build_leave_tab(wb, gd, T):
    ws = wb.create_sheet('Attendance & Leave')
    HEADER_ROW = 4

    ws.merge_cells('A1:M1')
    title = ws['A1']
    title.value = 'ATTENDANCE & LEAVE  —  Per-employee balances and monthly attendance %'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:M2')
    sub = ws['A2']
    sub.value = '   India: CL 12 + SL 12 + EL 18  •  US: PTO 15 + Sick 10  •  Balance = Entitled − Used (formula)'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    headers = ['Emp ID', 'Name', 'Geo', 'Dept', 'CL/PTO Ent.', 'CL/PTO Used', 'CL/PTO Bal.',
               'SL/Sick Ent.', 'SL/Sick Used', 'SL/Sick Bal.', 'EL Ent.', 'EL Used / Bal.', 'Attendance %']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=HEADER_ROW, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=10, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['NAVY'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[HEADER_ROW].height = 32

    data_start = HEADER_ROW + 1
    for i, l in enumerate(gd.leave_data):
        r = data_start + i
        ws.cell(row=r, column=1, value=l['id'])
        ws.cell(row=r, column=2, value=l['name'])
        ws.cell(row=r, column=3, value=l['geo'])
        ws.cell(row=r, column=4, value=l['dept'])
        ws.cell(row=r, column=5, value=l['cl_entitled'])
        ws.cell(row=r, column=6, value=l['cl_used'])
        # Balance as formula
        ws.cell(row=r, column=7, value=f'=E{r}-F{r}')
        ws.cell(row=r, column=8, value=l['sl_entitled'])
        ws.cell(row=r, column=9, value=l['sl_used'])
        ws.cell(row=r, column=10, value=f'=H{r}-I{r}')
        ws.cell(row=r, column=11, value=l['el_entitled'])
        # EL combined for display
        ws.cell(row=r, column=12, value=f'={l["el_used"]} / =K{r}-{l["el_used"]}' if l['el_entitled'] > 0 else 'N/A')
        # Actually simpler: just show balance as formula
        ws.cell(row=r, column=12, value=f'=K{r}-{l["el_used"]}')
        # Attendance %
        ws.cell(row=r, column=13, value=round(l['attendance_pct'], 1) / 100)
        ws.cell(row=r, column=13).number_format = '0.0%'

        # Styling
        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 14):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            if col in [2, 4]:
                cell.alignment = Alignment(horizontal='left', vertical='center', indent=1)
            else:
                cell.alignment = Alignment(horizontal='center', vertical='center')

    data_end = data_start + len(gd.leave_data) - 1

    # Column widths
    widths = [10, 22, 8, 16, 12, 12, 12, 13, 13, 12, 10, 14, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # Conditional formatting
    # Balance columns — low balance is amber/red
    for col_letter in ['G', 'J']:
        ws.conditional_formatting.add(f'{col_letter}{data_start}:{col_letter}{data_end}',
            CellIsRule(operator='lessThan', formula=['3'],
                       fill=PatternFill('solid', start_color=T['CORAL']),
                       font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))
        ws.conditional_formatting.add(f'{col_letter}{data_start}:{col_letter}{data_end}',
            CellIsRule(operator='between', formula=['3', '6'],
                       fill=PatternFill('solid', start_color=T['AMBER']),
                       font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    # Attendance % — data bar
    ws.conditional_formatting.add(f'M{data_start}:M{data_end}',
        DataBarRule(start_type='min', end_type='max', color=T['TEAL']))

    ws.freeze_panes = 'C5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['LeaveData'] = DefinedName('LeaveData',
        attr_text=f"'Attendance & Leave'!$A${data_start}:$M${data_end}")
    wb.defined_names['LeaveAttendance'] = DefinedName('LeaveAttendance',
        attr_text=f"'Attendance & Leave'!$M${data_start}:$M${data_end}")

    print(f"  Attendance & Leave tab: {len(gd.leave_data)} records.")


def build_goals_tab(wb, gd, T):
    ws = wb.create_sheet('Performance Goals')
    HEADER_ROW = 4

    ws.merge_cells('A1:K1')
    title = ws['A1']
    title.value = 'PERFORMANCE GOALS  —  KPIs, targets, achievement & weighted ratings'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:K2')
    sub = ws['A2']
    sub.value = '   Achievement % = Actual ÷ Target  •  Rating: 5★ ≥95%, 4★ 80-94%, 3★ 65-79%, 2★ 50-64%, 1★ <50%'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    headers = ['Goal ID', 'Emp ID', 'Name', 'Geo', 'Dept', 'Goal', 'Target', 'Actual', 'Achievement %', 'Rating', 'Status']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=HEADER_ROW, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=10, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['NAVY'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[HEADER_ROW].height = 30

    data_start = HEADER_ROW + 1
    for i, g in enumerate(gd.goals_data):
        r = data_start + i
        ws.cell(row=r, column=1, value=g['goal_id'])
        ws.cell(row=r, column=2, value=g['emp_id'])
        ws.cell(row=r, column=3, value=g['emp_name'])
        ws.cell(row=r, column=4, value=g['geo'])
        ws.cell(row=r, column=5, value=g['dept'])
        ws.cell(row=r, column=6, value=g['goal_title'])
        ws.cell(row=r, column=7, value=g['target'])
        ws.cell(row=r, column=8, value=g['actual'])
        # Achievement % as formula
        ws.cell(row=r, column=9, value=f'=IFERROR(H{r}/G{r},0)')
        ws.cell(row=r, column=9).number_format = '0%'
        # Rating as formula based on achievement
        ws.cell(row=r, column=10,
                value=f'=IF(I{r}>=0.95,5,IF(I{r}>=0.80,4,IF(I{r}>=0.65,3,IF(I{r}>=0.50,2,1))))')
        ws.cell(row=r, column=11, value=g['status'])

        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 12):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [3, 5, 6] else 'center',
                                         vertical='center',
                                         indent=1 if col in [3, 5, 6] else 0)

    data_end = data_start + len(gd.goals_data) - 1

    # Widths
    widths = [10, 10, 22, 8, 16, 26, 10, 10, 15, 10, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # CF: Achievement % data bar + color scale
    ws.conditional_formatting.add(f'I{data_start}:I{data_end}',
        DataBarRule(start_type='min', end_type='max', color=T['TEAL']))
    # Rating: color scale
    ws.conditional_formatting.add(f'J{data_start}:J{data_end}',
        ColorScaleRule(start_type='num', start_value=1, start_color='FEE2E2',
                       mid_type='num', mid_value=3, mid_color='FEF3C7',
                       end_type='num', end_value=5, end_color='86EFAC'))
    # Status colors
    for status, color in [('Completed', T['TEAL']), ('On Track', '3B82F6'), ('At Risk', T['CORAL'])]:
        ws.conditional_formatting.add(f'K{data_start}:K{data_end}',
            FormulaRule(formula=[f'$K{data_start}="{status}"'],
                        fill=PatternFill('solid', start_color=color),
                        font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    ws.freeze_panes = 'D5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['GoalsData'] = DefinedName('GoalsData',
        attr_text=f"'Performance Goals'!$A${data_start}:$K${data_end}")
    wb.defined_names['GoalsRating'] = DefinedName('GoalsRating',
        attr_text=f"'Performance Goals'!$J${data_start}:$J${data_end}")
    wb.defined_names['GoalsStatus'] = DefinedName('GoalsStatus',
        attr_text=f"'Performance Goals'!$K${data_start}:$K${data_end}")
    wb.defined_names['GoalsAchievement'] = DefinedName('GoalsAchievement',
        attr_text=f"'Performance Goals'!$I${data_start}:$I${data_end}")

    print(f"  Performance Goals tab: {len(gd.goals_data)} records.")


def build_recruitment_tab(wb, gd, T):
    ws = wb.create_sheet('Recruitment')
    HEADER_ROW = 4

    ws.merge_cells('A1:K1')
    title = ws['A1']
    title.value = 'RECRUITMENT  —  Open positions & candidate pipeline (ATS-style)'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:K2')
    sub = ws['A2']
    sub.value = '   Pipeline stages: Applied → Screened → Interviewed → Offered → Joined  •  Source-wise & priority tracked'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    # ===== Section 1: Open Positions =====
    pos_hdr = HEADER_ROW
    ws.merge_cells(start_row=pos_hdr, start_column=1, end_row=pos_hdr, end_column=11)
    h1 = ws.cell(row=pos_hdr, column=1, value='  OPEN POSITIONS')
    h1.font = Font(name=T['FONT'], bold=True, size=11, color=T['WHITE'])
    h1.fill = PatternFill('solid', start_color=T['NAVY'])
    h1.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[pos_hdr].height = 22

    pos_col_hdr = pos_hdr + 1
    pos_headers = ['Position ID', 'Title', 'Dept', 'Geo', 'Openings', 'Priority', 'Days Open', 'Applied', 'Screened', 'Interviewed', 'Offered']
    for i, h in enumerate(pos_headers, 1):
        c = ws.cell(row=pos_col_hdr, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=9, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['SLATE'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[pos_col_hdr].height = 28

    pos_data_start = pos_col_hdr + 1
    for i, p in enumerate(gd.open_positions):
        r = pos_data_start + i
        ws.cell(row=r, column=1, value=p['pos_id'])
        ws.cell(row=r, column=2, value=p['title'])
        ws.cell(row=r, column=3, value=p['dept'])
        ws.cell(row=r, column=4, value=p['geo'])
        ws.cell(row=r, column=5, value=p['openings'])
        ws.cell(row=r, column=6, value=p['priority'])
        ws.cell(row=r, column=7, value=p['days_open'])
        # Count candidates by stage for this position (live formula referring to candidate table below)
        # Will fix references after we know the candidate row range
        # For now, use COUNTIFS placeholders that we'll fill in
        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 12):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [2, 3] else 'center',
                                         vertical='center',
                                         indent=1 if col in [2, 3] else 0)

    pos_data_end = pos_data_start + len(gd.open_positions) - 1

    # ===== Section 2: Candidate Pipeline =====
    cand_section_start = pos_data_end + 3
    ws.merge_cells(start_row=cand_section_start, start_column=1, end_row=cand_section_start, end_column=11)
    h2 = ws.cell(row=cand_section_start, column=1, value='  CANDIDATE PIPELINE')
    h2.font = Font(name=T['FONT'], bold=True, size=11, color=T['WHITE'])
    h2.fill = PatternFill('solid', start_color=T['NAVY'])
    h2.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[cand_section_start].height = 22

    cand_col_hdr = cand_section_start + 1
    cand_headers = ['Candidate ID', 'Name', 'Position', 'Dept', 'Geo', 'Stage', 'Days in Stage', 'Source', 'Rating', '', '']
    for i, h in enumerate(cand_headers, 1):
        c = ws.cell(row=cand_col_hdr, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=9, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['SLATE'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[cand_col_hdr].height = 28

    cand_data_start = cand_col_hdr + 1
    for i, c in enumerate(gd.candidates):
        r = cand_data_start + i
        ws.cell(row=r, column=1, value=c['cand_id'])
        ws.cell(row=r, column=2, value=c['name'])
        ws.cell(row=r, column=3, value=c['pos_title'])
        ws.cell(row=r, column=4, value=c['dept'])
        ws.cell(row=r, column=5, value=c['geo'])
        ws.cell(row=r, column=6, value=c['stage'])
        ws.cell(row=r, column=7, value=c['days_in_stage'])
        ws.cell(row=r, column=8, value=c['source'])
        ws.cell(row=r, column=9, value=c['rating'] if c['rating'] > 0 else '')

        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 12):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [2, 3] else 'center',
                                         vertical='center',
                                         indent=1 if col in [2, 3] else 0)

    cand_data_end = cand_data_start + len(gd.candidates) - 1

    # Now go back and add the stage-count formulas to open positions
    for i, p in enumerate(gd.open_positions):
        r = pos_data_start + i
        pos_title = p['title'].replace('"', '""')
        # H: Applied count for this position
        ws.cell(row=r, column=8,
                value=f'=COUNTIFS($C${cand_data_start}:$C${cand_data_end},"{pos_title}",$F${cand_data_start}:$F${cand_data_end},"Applied")')
        ws.cell(row=r, column=9,
                value=f'=COUNTIFS($C${cand_data_start}:$C${cand_data_end},"{pos_title}",$F${cand_data_start}:$F${cand_data_end},"Screened")')
        ws.cell(row=r, column=10,
                value=f'=COUNTIFS($C${cand_data_start}:$C${cand_data_end},"{pos_title}",$F${cand_data_start}:$F${cand_data_end},"Interviewed")')
        ws.cell(row=r, column=11,
                value=f'=COUNTIFS($C${cand_data_start}:$C${cand_data_end},"{pos_title}",$F${cand_data_start}:$F${cand_data_end},"Offered")')

    # Widths
    widths = [12, 22, 22, 16, 8, 11, 12, 12, 12, 12, 11]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # CF: Priority colors
    for priority, color in [('High', T['CORAL']), ('Medium', T['AMBER']), ('Low', T['TEAL'])]:
        ws.conditional_formatting.add(f'F{pos_data_start}:F{pos_data_end}',
            FormulaRule(formula=[f'$F{pos_data_start}="{priority}"'],
                        fill=PatternFill('solid', start_color=color),
                        font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    # CF: Stage colors on candidate table
    stage_colors = {'Applied': '94A3B8', 'Screened': '3B82F6', 'Interviewed': '8B5CF6',
                    'Offered': T['AMBER'], 'Joined': T['TEAL']}
    for stage, color in stage_colors.items():
        ws.conditional_formatting.add(f'F{cand_data_start}:F{cand_data_end}',
            FormulaRule(formula=[f'$F{cand_data_start}="{stage}"'],
                        fill=PatternFill('solid', start_color=color),
                        font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    # Days open color scale (red if too long)
    ws.conditional_formatting.add(f'G{pos_data_start}:G{pos_data_end}',
        ColorScaleRule(start_type='num', start_value=0, start_color='86EFAC',
                       mid_type='num', mid_value=30, mid_color='FEF3C7',
                       end_type='num', end_value=60, end_color='FECACA'))

    ws.freeze_panes = 'A5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['OpenPositions'] = DefinedName('OpenPositions',
        attr_text=f"'Recruitment'!$A${pos_data_start}:$K${pos_data_end}")
    wb.defined_names['CandidateData'] = DefinedName('CandidateData',
        attr_text=f"'Recruitment'!$A${cand_data_start}:$I${cand_data_end}")
    wb.defined_names['CandidateStages'] = DefinedName('CandidateStages',
        attr_text=f"'Recruitment'!$F${cand_data_start}:$F${cand_data_end}")
    wb.defined_names['CandidateSources'] = DefinedName('CandidateSources',
        attr_text=f"'Recruitment'!$H${cand_data_start}:$H${cand_data_end}")
    wb.defined_names['PositionPriority'] = DefinedName('PositionPriority',
        attr_text=f"'Recruitment'!$F${pos_data_start}:$F${pos_data_end}")

    print(f"  Recruitment tab: {len(gd.open_positions)} positions + {len(gd.candidates)} candidates.")


def build_compliance_tab(wb, gd, T):
    ws = wb.create_sheet('Compliance Calendar')
    HEADER_ROW = 4

    ws.merge_cells('A1:I1')
    title = ws['A1']
    title.value = 'COMPLIANCE CALENDAR  —  Statutory deadlines & filings (India + US)'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:I2')
    sub = ws['A2']
    sub.value = '   Days Until = Due Date − Report Date  •  Status auto-classified: Overdue / Critical (≤7) / Upcoming (≤30) / Scheduled'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    headers = ['Compliance ID', 'Title', 'Category', 'Geo', 'Authority', 'Due Date', 'Frequency', 'Days Until', 'Status']
    for i, h in enumerate(headers, 1):
        c = ws.cell(row=HEADER_ROW, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=10, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['NAVY'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[HEADER_ROW].height = 30

    data_start = HEADER_ROW + 1
    # Sort by due date so soonest is first
    sorted_events = sorted(gd.compliance_events, key=lambda x: x['due_date'])
    for i, c in enumerate(sorted_events):
        r = data_start + i
        ws.cell(row=r, column=1, value=c['comp_id'])
        ws.cell(row=r, column=2, value=c['title'])
        ws.cell(row=r, column=3, value=c['category'])
        ws.cell(row=r, column=4, value=c['geo'])
        ws.cell(row=r, column=5, value=c['authority'])
        ws.cell(row=r, column=6, value=c['due_date'])
        ws.cell(row=r, column=6).number_format = 'dd-mmm-yyyy'
        ws.cell(row=r, column=7, value=c['frequency'])
        # Days until as live formula
        ws.cell(row=r, column=8, value=f'=F{r}-ReportDate')
        ws.cell(row=r, column=8).number_format = '0'
        # Status as live formula based on days
        ws.cell(row=r, column=9,
                value=f'=IF(H{r}<0,"Overdue",IF(H{r}<=7,"Critical",IF(H{r}<=30,"Upcoming","Scheduled")))')

        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 10):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [2, 3, 5] else 'center',
                                         vertical='center',
                                         indent=1 if col in [2, 3, 5] else 0)

    data_end = data_start + len(sorted_events) - 1

    # Widths
    widths = [14, 34, 14, 8, 22, 14, 12, 11, 12]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # CF: status colors
    for status, color in [('Overdue', '991B1B'), ('Critical', T['CORAL']),
                          ('Upcoming', T['AMBER']), ('Scheduled', T['TEAL'])]:
        ws.conditional_formatting.add(f'I{data_start}:I{data_end}',
            FormulaRule(formula=[f'$I{data_start}="{status}"'],
                        fill=PatternFill('solid', start_color=color),
                        font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    # Days until color scale
    ws.conditional_formatting.add(f'H{data_start}:H{data_end}',
        ColorScaleRule(start_type='num', start_value=-5, start_color='991B1B',
                       mid_type='num', mid_value=15, mid_color='FEF3C7',
                       end_type='num', end_value=90, end_color='86EFAC'))

    ws.freeze_panes = 'A5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['ComplianceData'] = DefinedName('ComplianceData',
        attr_text=f"'Compliance Calendar'!$A${data_start}:$I${data_end}")
    wb.defined_names['ComplianceDays'] = DefinedName('ComplianceDays',
        attr_text=f"'Compliance Calendar'!$H${data_start}:$H${data_end}")
    wb.defined_names['ComplianceStatus'] = DefinedName('ComplianceStatus',
        attr_text=f"'Compliance Calendar'!$I${data_start}:$I${data_end}")
    wb.defined_names['ComplianceGeo'] = DefinedName('ComplianceGeo',
        attr_text=f"'Compliance Calendar'!$D${data_start}:$D${data_end}")

    print(f"  Compliance Calendar tab: {len(sorted_events)} deadlines.")
    return sorted_events


def build_training_tab(wb, gd, T):
    ws = wb.create_sheet('Training & Skills')
    HEADER_ROW = 4

    ws.merge_cells('A1:I1')
    title = ws['A1']
    title.value = 'TRAINING & DEVELOPMENT  —  Programs, enrollments & completion tracking'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:I2')
    sub = ws['A2']
    sub.value = '   8 programs (4 mandatory)  •  Status: Not Started / In Progress / Completed  •  Completion % drives progress bars'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    # ===== Section 1: Training Programs Catalog =====
    prog_hdr = HEADER_ROW
    ws.merge_cells(start_row=prog_hdr, start_column=1, end_row=prog_hdr, end_column=9)
    h1 = ws.cell(row=prog_hdr, column=1, value='  TRAINING PROGRAMS CATALOG')
    h1.font = Font(name=T['FONT'], bold=True, size=11, color=T['WHITE'])
    h1.fill = PatternFill('solid', start_color=T['NAVY'])
    h1.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[prog_hdr].height = 22

    prog_col_hdr = prog_hdr + 1
    prog_headers = ['Train ID', 'Title', 'Category', 'Duration (hrs)', 'Mandatory', 'Target', 'Enrolled', 'Completed', 'Completion %']
    for i, h in enumerate(prog_headers, 1):
        c = ws.cell(row=prog_col_hdr, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=9, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['SLATE'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[prog_col_hdr].height = 28

    prog_data_start = prog_col_hdr + 1
    for i, p in enumerate(gd.training_programs):
        r = prog_data_start + i
        ws.cell(row=r, column=1, value=p['train_id'])
        ws.cell(row=r, column=2, value=p['title'])
        ws.cell(row=r, column=3, value=p['category'])
        ws.cell(row=r, column=4, value=p['duration_hrs'])
        ws.cell(row=r, column=5, value='✓ Yes' if p['mandatory'] else 'Optional')
        ws.cell(row=r, column=6, value=p['target'])
        # Counts will be computed after enrollment table is laid out
        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 10):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [2, 3, 6] else 'center',
                                         vertical='center',
                                         indent=1 if col in [2, 3, 6] else 0)

    prog_data_end = prog_data_start + len(gd.training_programs) - 1

    # ===== Section 2: Enrollment Records =====
    enroll_section_start = prog_data_end + 3
    ws.merge_cells(start_row=enroll_section_start, start_column=1, end_row=enroll_section_start, end_column=9)
    h2 = ws.cell(row=enroll_section_start, column=1, value='  EMPLOYEE ENROLLMENTS')
    h2.font = Font(name=T['FONT'], bold=True, size=11, color=T['WHITE'])
    h2.fill = PatternFill('solid', start_color=T['NAVY'])
    h2.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[enroll_section_start].height = 22

    enroll_col_hdr = enroll_section_start + 1
    enroll_headers = ['Enroll ID', 'Emp ID', 'Name', 'Geo', 'Dept', 'Program', 'Category', 'Completion %', 'Status']
    for i, h in enumerate(enroll_headers, 1):
        c = ws.cell(row=enroll_col_hdr, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=9, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['SLATE'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[enroll_col_hdr].height = 28

    enroll_data_start = enroll_col_hdr + 1
    for i, e in enumerate(gd.training_enrollments):
        r = enroll_data_start + i
        ws.cell(row=r, column=1, value=e['enroll_id'])
        ws.cell(row=r, column=2, value=e['emp_id'])
        ws.cell(row=r, column=3, value=e['emp_name'])
        ws.cell(row=r, column=4, value=e['geo'])
        ws.cell(row=r, column=5, value=e['dept'])
        ws.cell(row=r, column=6, value=e['train_title'])
        ws.cell(row=r, column=7, value=e['category'])
        ws.cell(row=r, column=8, value=e['completion_pct'] / 100)
        ws.cell(row=r, column=8).number_format = '0%'
        ws.cell(row=r, column=9, value=e['status'])

        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 10):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [3, 5, 6, 7] else 'center',
                                         vertical='center',
                                         indent=1 if col in [3, 5, 6, 7] else 0)

    enroll_data_end = enroll_data_start + len(gd.training_enrollments) - 1

    # Fill in catalog counts (live formulas referencing enrollment table)
    for i, p in enumerate(gd.training_programs):
        r = prog_data_start + i
        title_esc = p['title'].replace('"', '""')
        ws.cell(row=r, column=7,
                value=f'=COUNTIF($F${enroll_data_start}:$F${enroll_data_end},"{title_esc}")')
        ws.cell(row=r, column=8,
                value=f'=COUNTIFS($F${enroll_data_start}:$F${enroll_data_end},"{title_esc}",$I${enroll_data_start}:$I${enroll_data_end},"Completed")')
        ws.cell(row=r, column=9, value=f'=IFERROR(H{r}/G{r},0)')
        ws.cell(row=r, column=9).number_format = '0%'

    # Widths
    widths = [11, 11, 22, 8, 16, 28, 14, 13, 13]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # CF
    # Completion % data bars (both catalog and enrollments)
    ws.conditional_formatting.add(f'I{prog_data_start}:I{prog_data_end}',
        DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color=T['TEAL']))
    ws.conditional_formatting.add(f'H{enroll_data_start}:H{enroll_data_end}',
        DataBarRule(start_type='num', start_value=0, end_type='num', end_value=1, color=T['TEAL']))

    # Status colors
    for status, color in [('Completed', T['TEAL']), ('In Progress', '3B82F6'), ('Not Started', T['CORAL'])]:
        ws.conditional_formatting.add(f'I{enroll_data_start}:I{enroll_data_end}',
            FormulaRule(formula=[f'$I{enroll_data_start}="{status}"'],
                        fill=PatternFill('solid', start_color=color),
                        font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    ws.freeze_panes = 'A5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['TrainingPrograms'] = DefinedName('TrainingPrograms',
        attr_text=f"'Training & Skills'!$A${prog_data_start}:$I${prog_data_end}")
    wb.defined_names['TrainingEnrollments'] = DefinedName('TrainingEnrollments',
        attr_text=f"'Training & Skills'!$A${enroll_data_start}:$I${enroll_data_end}")
    wb.defined_names['EnrollmentStatus'] = DefinedName('EnrollmentStatus',
        attr_text=f"'Training & Skills'!$I${enroll_data_start}:$I${enroll_data_end}")
    wb.defined_names['EnrollmentCompletion'] = DefinedName('EnrollmentCompletion',
        attr_text=f"'Training & Skills'!$H${enroll_data_start}:$H${enroll_data_end}")

    print(f"  Training & Skills tab: {len(gd.training_programs)} programs + {len(gd.training_enrollments)} enrollments.")


def build_attrition_risk_tab(wb, gd, T):
    ws = wb.create_sheet('Attrition Risk')
    HEADER_ROW = 4

    ws.merge_cells('A1:L1')
    title = ws['A1']
    title.value = 'ATTRITION RISK MODEL  —  Predictive scoring per employee'
    title.font = Font(name=T['FONT'], bold=True, size=14, color=T['WHITE'])
    title.fill = PatternFill('solid', start_color=T['NAVY'])
    title.alignment = Alignment(horizontal='left', vertical='center', indent=1)
    ws.row_dimensions[1].height = 28

    ws.merge_cells('A2:L2')
    sub = ws['A2']
    sub.value = '   Total = Tenure + Productivity + Comp-Ratio + Other factors  •  High ≥65, Medium 35-64, Low <35'
    sub.font = Font(name=T['FONT'], italic=True, size=9, color=T['SLATE'])
    sub.fill = PatternFill('solid', start_color=T['LIGHT_BG'])
    sub.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[2].height = 18

    headers = ['Emp ID', 'Name', 'Geo', 'Dept', 'Designation', 'Manager',
               'Tenure (days)', 'Productivity', 'Comp Ratio', 'Other', 'Total Score', 'Risk Level', 'Top Reason']
    # 13 headers, let me adjust merge
    ws.merge_cells('A1:M1')
    ws.merge_cells('A2:M2')

    for i, h in enumerate(headers, 1):
        c = ws.cell(row=HEADER_ROW, column=i, value=h)
        c.font = Font(name=T['FONT'], bold=True, size=10, color=T['WHITE'])
        c.fill = PatternFill('solid', start_color=T['NAVY'])
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    ws.row_dimensions[HEADER_ROW].height = 36

    data_start = HEADER_ROW + 1
    for i, a in enumerate(gd.attrition_risk):
        r = data_start + i
        ws.cell(row=r, column=1, value=a['id'])
        ws.cell(row=r, column=2, value=a['name'])
        ws.cell(row=r, column=3, value=a['geo'])
        ws.cell(row=r, column=4, value=a['dept'])
        ws.cell(row=r, column=5, value=a['desig'])
        ws.cell(row=r, column=6, value=a['manager'])
        ws.cell(row=r, column=7, value=a['tenure_days'])
        ws.cell(row=r, column=8, value=a['prod_score'])
        ws.cell(row=r, column=9, value=a['comp_score'])
        ws.cell(row=r, column=10, value=a['other_score'])
        # Total = sum of components (live formula so editing components updates total)
        ws.cell(row=r, column=11, value=f'=H{r}+I{r}+J{r}+MIN(50,G{r}/365*0.8*10+IF(G{r}<180,50,IF(G{r}<540,30,IF(G{r}<1080,15,8))))')
        # Actually simpler: store tenure score component separately. Let me redo:
        # Components H = prod, I = comp, J = other, and G holds tenure days.
        # Total = H+I+J + tenure_score (which we computed). Let me store tenure_score in a hidden column or just hardcode it.
        # Simplest: just store the total as a value but make Risk Level a formula
        ws.cell(row=r, column=11, value=a['total_score'])
        # Risk Level as live formula based on total
        ws.cell(row=r, column=12,
                value=f'=IF(K{r}>=65,"High",IF(K{r}>=35,"Medium","Low"))')
        ws.cell(row=r, column=13, value=a['top_reason'])

        bg = T['LIGHT_BG'] if i % 2 == 1 else T['WHITE']
        for col in range(1, 14):
            cell = ws.cell(row=r, column=col)
            cell.fill = PatternFill('solid', start_color=bg)
            cell.font = Font(name=T['FONT'], size=9, color=T['DARK_TEXT'])
            cell.alignment = Alignment(horizontal='left' if col in [2, 4, 5, 6, 13] else 'center',
                                         vertical='center',
                                         indent=1 if col in [2, 4, 5, 6, 13] else 0)

    data_end = data_start + len(gd.attrition_risk) - 1

    # Widths
    widths = [10, 22, 8, 14, 22, 22, 12, 12, 11, 9, 11, 11, 18]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[chr(64 + i)].width = w

    # CF
    # Total score color scale
    ws.conditional_formatting.add(f'K{data_start}:K{data_end}',
        ColorScaleRule(start_type='num', start_value=0, start_color='86EFAC',
                       mid_type='num', mid_value=40, mid_color='FEF3C7',
                       end_type='num', end_value=85, end_color='FECACA'))
    # Risk level colors
    for level, color in [('High', T['CORAL']), ('Medium', T['AMBER']), ('Low', T['TEAL'])]:
        ws.conditional_formatting.add(f'L{data_start}:L{data_end}',
            FormulaRule(formula=[f'$L{data_start}="{level}"'],
                        fill=PatternFill('solid', start_color=color),
                        font=Font(name=T['FONT'], bold=True, color=T['WHITE'])))

    ws.freeze_panes = 'C5'
    ws.sheet_view.showGridLines = False

    # Named ranges
    wb.defined_names['AttritionRiskData'] = DefinedName('AttritionRiskData',
        attr_text=f"'Attrition Risk'!$A${data_start}:$M${data_end}")
    wb.defined_names['AttritionRiskLevel'] = DefinedName('AttritionRiskLevel',
        attr_text=f"'Attrition Risk'!$L${data_start}:$L${data_end}")
    wb.defined_names['AttritionRiskScore'] = DefinedName('AttritionRiskScore',
        attr_text=f"'Attrition Risk'!$K${data_start}:$K${data_end}")
    wb.defined_names['AttritionRiskGeo'] = DefinedName('AttritionRiskGeo',
        attr_text=f"'Attrition Risk'!$C${data_start}:$C${data_end}")
    wb.defined_names['AttritionRiskDept'] = DefinedName('AttritionRiskDept',
        attr_text=f"'Attrition Risk'!$D${data_start}:$D${data_end}")

    print(f"  Attrition Risk tab: {len(gd.attrition_risk)} employees scored.")


def build_all_extensions(wb, gd, T):
    """Build all 7 extension tabs. Returns dict of tab metadata."""
    print("\nBuilding extension tabs...")
    build_payroll_tab(wb, gd, T)
    build_leave_tab(wb, gd, T)
    build_goals_tab(wb, gd, T)
    build_recruitment_tab(wb, gd, T)
    build_compliance_tab(wb, gd, T)
    build_training_tab(wb, gd, T)
    build_attrition_risk_tab(wb, gd, T)
    print("All extension tabs built.\n")
