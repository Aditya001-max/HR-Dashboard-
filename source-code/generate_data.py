"""
HR Dashboard - Sample Data Generator
Generates realistic employee data for India & US offices.
"""
import random
from datetime import date, timedelta

random.seed(42)  # reproducible

DEPARTMENTS = ['Engineering', 'Product', 'Sales', 'Marketing', 'HR', 'Finance', 'Operations', 'Customer Success']
DESIGNATIONS = {
    'Engineering': ['SDE-1', 'SDE-2', 'SDE-3', 'Engineering Manager', 'Principal Engineer', 'Engineering Intern'],
    'Product': ['Associate PM', 'Product Manager', 'Senior PM', 'Director of Product', 'Product Intern'],
    'Sales': ['SDR', 'Account Executive', 'Senior AE', 'Sales Manager', 'VP Sales', 'Sales Intern'],
    'Marketing': ['Marketing Associate', 'Marketing Manager', 'Senior Marketing Manager', 'CMO', 'Marketing Intern'],
    'HR': ['HR Executive', 'HR Manager', 'HR Business Partner', 'CHRO', 'HR Intern'],
    'Finance': ['Financial Analyst', 'Senior Analyst', 'Finance Manager', 'CFO', 'Finance Intern'],
    'Operations': ['Ops Associate', 'Ops Manager', 'Senior Ops Manager', 'COO', 'Ops Intern'],
    'Customer Success': ['CSM', 'Senior CSM', 'CS Manager', 'VP Customer Success', 'CS Intern'],
}
SKILLSETS = {
    'Engineering': ['Python, AWS', 'Java, Spring', 'React, Node', 'Go, Kubernetes', 'iOS, Swift', 'Android, Kotlin', 'Data Engineering', 'ML/AI'],
    'Product': ['Product Strategy', 'Roadmapping', 'User Research', 'Analytics', 'Agile/Scrum'],
    'Sales': ['Enterprise Sales', 'Inside Sales', 'Channel Sales', 'SaaS Sales', 'Account Management'],
    'Marketing': ['Content Marketing', 'SEO/SEM', 'Brand Marketing', 'Demand Gen', 'Marketing Automation'],
    'HR': ['Talent Acquisition', 'L&D', 'Comp & Ben', 'HRBP', 'Employee Relations'],
    'Finance': ['FP&A', 'Accounting', 'Tax', 'Treasury', 'Audit'],
    'Operations': ['Supply Chain', 'Process Excellence', 'Vendor Mgmt', 'Logistics'],
    'Customer Success': ['Onboarding', 'Account Management', 'Renewals', 'Support Mgmt'],
}

INDIA_FIRST = ['Aarav','Vivaan','Aditya','Vihaan','Arjun','Sai','Reyansh','Krishna','Ishaan','Shaurya',
               'Ananya','Diya','Aadhya','Saanvi','Aaradhya','Anika','Navya','Kiara','Myra','Sara',
               'Rohan','Karan','Nikhil','Rahul','Sanjay','Priya','Neha','Pooja','Riya','Kavya',
               'Vikram','Ravi','Amit','Suresh','Deepak','Meera','Anjali','Divya','Sneha','Shreya']
INDIA_LAST = ['Sharma','Verma','Patel','Gupta','Singh','Kumar','Reddy','Iyer','Nair','Menon',
              'Khan','Joshi','Mehta','Shah','Agarwal','Bose','Chatterjee','Das','Pillai','Rao']

US_FIRST = ['James','Mary','Robert','Patricia','John','Jennifer','Michael','Linda','David','Elizabeth',
            'William','Barbara','Richard','Susan','Joseph','Jessica','Thomas','Sarah','Charles','Karen',
            'Christopher','Nancy','Daniel','Lisa','Matthew','Margaret','Anthony','Betty','Donald','Sandra',
            'Mark','Ashley','Paul','Kimberly','Steven','Emily','Andrew','Donna','Kenneth','Michelle']
US_LAST = ['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez',
           'Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin']

today = date(2026, 5, 11)

def rand_date(start_year, end_year):
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def fmt(d):
    return d.strftime('%d-%b-%Y')

# ========== INDIA EMPLOYEES ==========
india_employees = []
emp_id = 1001
managers_india = []  # track senior employees to be reporting managers

# First create senior employees (managers)
senior_pool = []
for dept in DEPARTMENTS:
    # 1 head per dept
    head_desig = DESIGNATIONS[dept][-2]  # second-to-last is usually the head
    fn = random.choice(INDIA_FIRST); ln = random.choice(INDIA_LAST)
    senior_pool.append({
        'id': f'IND{emp_id}', 'name': f'{fn} {ln}', 'dept': dept,
        'desig': head_desig, 'manager': 'CEO - Ramesh Krishnan',
        'skill': random.choice(SKILLSETS[dept]), 'doj': rand_date(2015, 2019),
        'status': 'Confirmed', 'lwd': '', 'intern_end': ''
    })
    emp_id += 1

# Then add team members under each head
heads_only = list(senior_pool)  # snapshot before we append
for head in heads_only:
    dept = head['dept']
    # 2-3 mid-managers per dept
    n_mid = random.randint(2, 3)
    for _ in range(n_mid):
        mid_desig = DESIGNATIONS[dept][2] if len(DESIGNATIONS[dept]) > 3 else DESIGNATIONS[dept][1]
        fn = random.choice(INDIA_FIRST); ln = random.choice(INDIA_LAST)
        mid = {
            'id': f'IND{emp_id}', 'name': f'{fn} {ln}', 'dept': dept,
            'desig': mid_desig, 'manager': head['name'],
            'skill': random.choice(SKILLSETS[dept]), 'doj': rand_date(2018, 2022),
            'status': 'Confirmed', 'lwd': '', 'intern_end': ''
        }
        senior_pool.append(mid)
        emp_id += 1

india_employees.extend(senior_pool)

# Now ICs and interns
for head in [s for s in senior_pool if s['manager'] == 'CEO - Ramesh Krishnan']:
    dept = head['dept']
    mids = [s for s in senior_pool if s['manager'] == head['name']]
    if not mids:
        mids = [head]
    # 4-6 ICs per dept
    n_ic = random.randint(4, 6)
    for i in range(n_ic):
        mgr = random.choice(mids)
        ic_desig = random.choice(DESIGNATIONS[dept][:2])  # junior desigs
        fn = random.choice(INDIA_FIRST); ln = random.choice(INDIA_LAST)
        # First 2 ICs in each dept: recent hires (probation candidates)
        if i < 2:
            # Probation confirms at 180 days from DOJ
            # Some need confirmation in next 30 days (joined ~150-179 days ago)
            # Some are mid-probation (joined 30-150 days ago)
            if random.random() < 0.5:
                # Coming due for confirmation in next 30 days
                doj = today - timedelta(days=random.randint(151, 179))
            else:
                doj = today - timedelta(days=random.randint(30, 149))
            status = 'Under Probation'
        else:
            doj = rand_date(2022, 2024)
            status = 'Confirmed'
        india_employees.append({
            'id': f'IND{emp_id}', 'name': f'{fn} {ln}', 'dept': dept,
            'desig': ic_desig, 'manager': mgr['name'],
            'skill': random.choice(SKILLSETS[dept]), 'doj': doj,
            'status': status, 'lwd': '', 'intern_end': ''
        })
        emp_id += 1
    # 1-2 interns per dept
    n_intern = random.randint(1, 2)
    for _ in range(n_intern):
        mgr = random.choice(mids)
        intern_desig = [d for d in DESIGNATIONS[dept] if 'Intern' in d][0]
        fn = random.choice(INDIA_FIRST); ln = random.choice(INDIA_LAST)
        doj = rand_date(2025, 2026)
        # Intern end date: 3-6 months from DOJ; some ending in next 45 days for alerts
        intern_end = doj + timedelta(days=random.randint(90, 180))
        # Force a few interns to end within next 45 days
        if random.random() < 0.4:
            intern_end = today + timedelta(days=random.randint(5, 44))
        india_employees.append({
            'id': f'IND{emp_id}', 'name': f'{fn} {ln}', 'dept': dept,
            'desig': intern_desig, 'manager': mgr['name'],
            'skill': random.choice(SKILLSETS[dept]), 'doj': doj,
            'status': 'Intern', 'lwd': '', 'intern_end': intern_end
        })
        emp_id += 1

# ========== US EMPLOYEES ==========
us_employees = []
emp_id_us = 2001
us_senior_pool = []
for dept in DEPARTMENTS[:6]:  # US has fewer depts
    head_desig = DESIGNATIONS[dept][-2]
    fn = random.choice(US_FIRST); ln = random.choice(US_LAST)
    us_senior_pool.append({
        'id': f'US{emp_id_us}', 'name': f'{fn} {ln}', 'dept': dept,
        'desig': head_desig, 'manager': 'CEO - Ramesh Krishnan',
        'skill': random.choice(SKILLSETS[dept]), 'doj': rand_date(2016, 2020),
        'status': 'Confirmed', 'allocation': 100, 'lwd': '', 'intern_end': ''
    })
    emp_id_us += 1

us_heads_only = list(us_senior_pool)
for head in us_heads_only:
    dept = head['dept']
    n_mid = random.randint(1, 2)
    for _ in range(n_mid):
        mid_desig = DESIGNATIONS[dept][2] if len(DESIGNATIONS[dept]) > 3 else DESIGNATIONS[dept][1]
        fn = random.choice(US_FIRST); ln = random.choice(US_LAST)
        mid = {
            'id': f'US{emp_id_us}', 'name': f'{fn} {ln}', 'dept': dept,
            'desig': mid_desig, 'manager': head['name'],
            'skill': random.choice(SKILLSETS[dept]), 'doj': rand_date(2019, 2023),
            'status': 'Confirmed', 'allocation': 100, 'lwd': '', 'intern_end': ''
        }
        us_senior_pool.append(mid)
        emp_id_us += 1

us_employees.extend(us_senior_pool)

for head in [s for s in us_senior_pool if s['manager'] == 'CEO - Ramesh Krishnan']:
    dept = head['dept']
    mids = [s for s in us_senior_pool if s['manager'] == head['name']]
    if not mids:
        mids = [head]
    n_ic = random.randint(2, 4)
    for i in range(n_ic):
        mgr = random.choice(mids)
        ic_desig = random.choice(DESIGNATIONS[dept][:2])
        fn = random.choice(US_FIRST); ln = random.choice(US_LAST)
        if i < 1:
            if random.random() < 0.5:
                doj = today - timedelta(days=random.randint(151, 179))
            else:
                doj = today - timedelta(days=random.randint(30, 149))
            status = 'Under Probation'
        else:
            doj = rand_date(2022, 2024)
            status = 'Confirmed'
        # Allocation can be partial for US
        alloc = random.choice([100, 100, 100, 75, 50])
        us_employees.append({
            'id': f'US{emp_id_us}', 'name': f'{fn} {ln}', 'dept': dept,
            'desig': ic_desig, 'manager': mgr['name'],
            'skill': random.choice(SKILLSETS[dept]), 'doj': doj,
            'status': status, 'allocation': alloc, 'lwd': '', 'intern_end': ''
        })
        emp_id_us += 1
    # 1 intern per dept in US
    if random.random() < 0.7:
        mgr = random.choice(mids)
        intern_desig = [d for d in DESIGNATIONS[dept] if 'Intern' in d][0]
        fn = random.choice(US_FIRST); ln = random.choice(US_LAST)
        doj = rand_date(2025, 2026)
        intern_end = doj + timedelta(days=random.randint(90, 180))
        if random.random() < 0.3:
            intern_end = today + timedelta(days=random.randint(5, 44))
        us_employees.append({
            'id': f'US{emp_id_us}', 'name': f'{fn} {ln}', 'dept': dept,
            'desig': intern_desig, 'manager': mgr['name'],
            'skill': random.choice(SKILLSETS[dept]), 'doj': doj,
            'status': 'Intern', 'allocation': 100, 'lwd': '', 'intern_end': intern_end
        })
        emp_id_us += 1

# ========== OFFBOARDED ==========
offboarded = []
# Generate exits across quarters for attrition calc
# Q1 2026, Q4 2025, Q3 2025, Q2 2025
reasons = ['Resignation', 'Better Opportunity', 'Personal Reasons', 'Performance', 'Relocation', 'Higher Studies', 'Termination']

# Pull some random employees from both DBs to mark as offboarded
# We'll create separate offboarded records (different from active employees)
off_id = 9001
quarters = [
    (date(2025, 4, 1), date(2025, 6, 30), 'Q2-2025'),
    (date(2025, 7, 1), date(2025, 9, 30), 'Q3-2025'),
    (date(2025, 10, 1), date(2025, 12, 31), 'Q4-2025'),
    (date(2026, 1, 1), date(2026, 3, 31), 'Q1-2026'),
    (date(2026, 4, 1), date(2026, 5, 11), 'Q2-2026'),
]
for q_start, q_end, q_label in quarters:
    n_exits = random.randint(3, 8)
    for _ in range(n_exits):
        is_india = random.random() < 0.7
        if is_india:
            fn = random.choice(INDIA_FIRST); ln = random.choice(INDIA_LAST)
            geo = 'India'
            eid = f'IND{off_id}'
        else:
            fn = random.choice(US_FIRST); ln = random.choice(US_LAST)
            geo = 'US'
            eid = f'US{off_id}'
        dept = random.choice(DEPARTMENTS)
        desig = random.choice(DESIGNATIONS[dept][:3])
        doj = rand_date(2019, 2024)
        lwd = q_start + timedelta(days=random.randint(0, (q_end - q_start).days))
        tenure_days = (lwd - doj).days
        offboarded.append({
            'id': eid, 'name': f'{fn} {ln}', 'geo': geo, 'dept': dept,
            'desig': desig, 'doj': doj, 'lwd': lwd, 'quarter': q_label,
            'reason': random.choice(reasons), 'tenure_years': round(tenure_days/365.25, 2)
        })
        off_id += 1

# ========== RM DATA (Resource Allocation - monthly) ==========
# For each US employee, monthly allocation data
months_rm = ['Jan-2026', 'Feb-2026', 'Mar-2026', 'Apr-2026', 'May-2026']
rm_data = []
for emp in us_employees:
    if emp['status'] == 'Intern':
        # Track intern internship end
        for m in months_rm:
            rm_data.append({
                'id': emp['id'], 'name': emp['name'], 'dept': emp['dept'],
                'month': m, 'allocation': emp['allocation'],
                'lwd_intern_end': emp['intern_end']
            })
    else:
        for m in months_rm:
            # Slight variation in allocation
            alloc = emp['allocation'] + random.choice([-10, -5, 0, 0, 0, 5])
            alloc = max(50, min(100, alloc))
            rm_data.append({
                'id': emp['id'], 'name': emp['name'], 'dept': emp['dept'],
                'month': m, 'allocation': alloc,
                'lwd_intern_end': ''
            })

# ========== FINANCE - CTC ==========
finance_data = []
# Salary bands by designation level (in INR for India, USD for US)
def get_ctc_india(desig):
    if 'Intern' in desig: return random.randint(25000, 50000) * 12  # monthly stipend * 12
    if 'CEO' in desig or 'CFO' in desig or 'CMO' in desig or 'COO' in desig or 'CHRO' in desig: return random.randint(8000000, 15000000)
    if 'Director' in desig or 'VP' in desig: return random.randint(5000000, 8000000)
    if 'Principal' in desig or 'Manager' in desig and 'Senior' in desig: return random.randint(3500000, 5500000)
    if 'Manager' in desig: return random.randint(2500000, 4000000)
    if 'Senior' in desig or '-3' in desig: return random.randint(1800000, 3000000)
    if '-2' in desig or 'Analyst' in desig: return random.randint(1200000, 2000000)
    return random.randint(600000, 1200000)

def get_ctc_us(desig):
    if 'Intern' in desig: return random.randint(40000, 70000)
    if 'CEO' in desig or 'CFO' in desig or 'CMO' in desig or 'COO' in desig or 'CHRO' in desig: return random.randint(250000, 450000)
    if 'Director' in desig or 'VP' in desig: return random.randint(180000, 280000)
    if 'Principal' in desig: return random.randint(180000, 240000)
    if 'Manager' in desig and 'Senior' in desig: return random.randint(140000, 200000)
    if 'Manager' in desig: return random.randint(110000, 160000)
    if 'Senior' in desig: return random.randint(120000, 170000)
    return random.randint(70000, 120000)

USD_TO_INR = 83.5

for emp in india_employees:
    ctc_inr = get_ctc_india(emp['desig'])
    finance_data.append({
        'id': emp['id'], 'name': emp['name'], 'geo': 'India', 'dept': emp['dept'],
        'desig': emp['desig'],
        'annual_inr': ctc_inr, 'monthly_inr': round(ctc_inr/12),
        'annual_usd': round(ctc_inr/USD_TO_INR), 'monthly_usd': round(ctc_inr/USD_TO_INR/12)
    })

for emp in us_employees:
    ctc_usd = get_ctc_us(emp['desig'])
    # Pro-rate by allocation
    effective = ctc_usd * (emp['allocation'] / 100)
    finance_data.append({
        'id': emp['id'], 'name': emp['name'], 'geo': 'US', 'dept': emp['dept'],
        'desig': emp['desig'],
        'annual_usd': effective, 'monthly_usd': round(effective/12),
        'annual_inr': round(effective*USD_TO_INR), 'monthly_inr': round(effective*USD_TO_INR/12)
    })

# ========== PRODUCTIVITY ==========
# Per-resource productivity average (1-5 scale)
productivity_data = []
for emp in india_employees + us_employees:
    if emp['status'] != 'Intern':
        score = round(random.uniform(2.8, 4.9), 2)
    else:
        score = round(random.uniform(2.5, 4.5), 2)
    productivity_data.append({
        'id': emp['id'], 'name': emp['name'],
        'geo': 'India' if emp['id'].startswith('IND') else 'US',
        'dept': emp['dept'], 'desig': emp['desig'],
        'score': score,
        'tasks_completed': random.randint(15, 80),
        'on_time_pct': round(random.uniform(60, 99), 1)
    })

# ========== RISK REPORT ==========
risk_data = []
risk_categories = ['Performance Risk', 'Flight Risk', 'Compliance Risk', 'Skill Gap', 'Visa/Documentation', 'Manager Conflict', 'Workload/Burnout']
risk_levels = ['High', 'Medium', 'Low']
risk_status = ['Open', 'Under Review', 'Mitigation in Progress', 'Closed']

# Pick ~12-15 employees with risks
all_emps_for_risk = random.sample(india_employees + us_employees, 15)
risk_id = 1
for emp in all_emps_for_risk:
    risk_data.append({
        'risk_id': f'RSK-{risk_id:03d}',
        'emp_id': emp['id'], 'emp_name': emp['name'],
        'geo': 'India' if emp['id'].startswith('IND') else 'US',
        'dept': emp['dept'],
        'category': random.choice(risk_categories),
        'level': random.choices(risk_levels, weights=[2, 4, 3])[0],
        'raised_on': rand_date(2025, 2026),
        'status': random.choices(risk_status, weights=[2, 2, 3, 1])[0],
        'owner': emp['manager'] if emp['manager'] != 'CEO - Ramesh Krishnan' else 'HR Team',
        'notes': random.choice([
            'Performance below expectations for 2 consecutive cycles',
            'Indicated interest in external opportunities',
            'Pending compliance training completion',
            'Skill upgrade recommended for upcoming project',
            'Visa renewal in progress',
            'Reassignment under consideration',
            'High workload reported in last 1:1'
        ])
    })
    risk_id += 1

# Export to a module-level dict for the workbook builder
DATA = {
    'india': india_employees,
    'us': us_employees,
    'offboarded': offboarded,
    'rm': rm_data,
    'finance': finance_data,
    'productivity': productivity_data,
    'risk': risk_data,
    'today': today
}

if __name__ == '__main__':
    print(f"India employees: {len(india_employees)}")
    print(f"US employees: {len(us_employees)}")
    print(f"Offboarded: {len(offboarded)}")
    print(f"RM data rows: {len(rm_data)}")
    print(f"Finance rows: {len(finance_data)}")
    print(f"Productivity rows: {len(productivity_data)}")
    print(f"Risk rows: {len(risk_data)}")
    # Sample
    print("\nSample India employee:", india_employees[0])
    print("Sample intern:", [e for e in india_employees if e['status']=='Intern'][0])
    # Count alerts
    interns_45 = [e for e in india_employees + us_employees if e['status']=='Intern' and isinstance(e['intern_end'], date) and 0 <= (e['intern_end']-today).days <= 45]
    probation = [e for e in india_employees + us_employees if e['status']=='Under Probation']
    print(f"\nInterns ending in 45 days: {len(interns_45)}")
    print(f"Under Probation: {len(probation)}")

# ============================================================
# EXTENDED DATA: Payroll, Leave, Goals, Recruitment, Compliance, Training
# ============================================================
import random as _r2
_r2.seed(42)

# Build a CTC for each active employee
ctc_inr_by_id = {}  # india employees
ctc_usd_by_id = {}  # us employees

# Salary bands by designation seniority
def _india_ctc_for(emp):
    desig = emp['desig'].lower()
    if any(t in desig for t in ['principal', 'director', 'vp', 'cmo', 'cfo', 'coo', 'chro']):
        return _r2.randint(3500000, 6500000)
    elif any(t in desig for t in ['senior', 'lead', 'manager']):
        return _r2.randint(1800000, 3200000)
    elif 'intern' in desig:
        return _r2.randint(360000, 540000)
    else:
        return _r2.randint(800000, 1700000)

def _us_ctc_for(emp):
    desig = emp['desig'].lower()
    if any(t in desig for t in ['principal', 'director', 'vp', 'cmo', 'cfo', 'coo', 'chro']):
        return _r2.randint(180000, 280000)
    elif any(t in desig for t in ['senior', 'lead', 'manager']):
        return _r2.randint(120000, 175000)
    elif 'intern' in desig:
        return _r2.randint(45000, 65000)
    else:
        return _r2.randint(75000, 115000)

for e in india_employees:
    if e['status'] != 'Offboarded':
        ctc_inr_by_id[e['id']] = _india_ctc_for(e)

for e in us_employees:
    if e['status'] != 'Offboarded':
        ctc_usd_by_id[e['id']] = _us_ctc_for(e)

# ----- PAYROLL DATA -----
# For India: Basic 40%, HRA 20%, Special = rest. PF 12% of Basic each side, ESI if gross<=21k/mo,
# Professional Tax flat 200, TDS approx 5-15% based on annual CTC slabs (new regime)
payroll_data = []
for e in india_employees:
    if e['status'] == 'Offboarded':
        continue
    ctc = ctc_inr_by_id[e['id']]
    basic_y = round(ctc * 0.40)
    hra_y = round(ctc * 0.20)
    special_y = ctc - basic_y - hra_y
    monthly_basic = round(basic_y / 12)
    monthly_hra = round(hra_y / 12)
    monthly_special = round(special_y / 12)
    monthly_gross = monthly_basic + monthly_hra + monthly_special
    pf_emp = round(monthly_basic * 0.12)
    pf_emr = round(monthly_basic * 0.12)
    esi_emp = round(monthly_gross * 0.0075) if monthly_gross <= 21000 else 0
    pt = 200
    # TDS slabs (new regime approx, monthly)
    if ctc <= 300000:
        tds_m = 0
    elif ctc <= 700000:
        tds_m = round((ctc - 300000) * 0.05 / 12)
    elif ctc <= 1000000:
        tds_m = round((20000 + (ctc - 700000) * 0.10) / 12)
    elif ctc <= 1200000:
        tds_m = round((50000 + (ctc - 1000000) * 0.15) / 12)
    elif ctc <= 1500000:
        tds_m = round((80000 + (ctc - 1200000) * 0.20) / 12)
    else:
        tds_m = round((140000 + (ctc - 1500000) * 0.30) / 12)
    net = monthly_gross - pf_emp - esi_emp - pt - tds_m
    payroll_data.append({
        'id': e['id'], 'name': e['name'], 'geo': 'India', 'dept': e['dept'],
        'ctc': ctc, 'basic': monthly_basic, 'hra': monthly_hra, 'special': monthly_special,
        'gross': monthly_gross, 'pf_emp': pf_emp, 'pf_emr': pf_emr,
        'esi': esi_emp, 'pt': pt, 'tds': tds_m, 'net': net,
        'currency': 'INR'
    })

for e in us_employees:
    if e['status'] == 'Offboarded':
        continue
    ctc = ctc_usd_by_id[e['id']]
    monthly_gross = round(ctc / 12)
    # No basic/HRA split for US — single gross
    # Federal tax bracket simulation (rough)
    if ctc <= 11600:
        fed_rate = 0.10
    elif ctc <= 47150:
        fed_rate = 0.12
    elif ctc <= 100525:
        fed_rate = 0.22
    elif ctc <= 191950:
        fed_rate = 0.24
    elif ctc <= 243725:
        fed_rate = 0.32
    else:
        fed_rate = 0.35
    fed_tax = round(monthly_gross * fed_rate)
    ss = round(monthly_gross * 0.062)
    medicare = round(monthly_gross * 0.0145)
    state_tax = round(monthly_gross * 0.05)  # avg state rate
    net = monthly_gross - fed_tax - ss - medicare - state_tax
    payroll_data.append({
        'id': e['id'], 'name': e['name'], 'geo': 'US', 'dept': e['dept'],
        'ctc': ctc, 'basic': monthly_gross, 'hra': 0, 'special': 0,
        'gross': monthly_gross, 'pf_emp': fed_tax, 'pf_emr': 0,  # repurposed columns
        'esi': ss, 'pt': medicare, 'tds': state_tax, 'net': net,
        'currency': 'USD'
    })

print(f"Payroll data: {len(payroll_data)} records")

# ----- LEAVE BALANCE DATA -----
leave_data = []
for e in india_employees:
    if e['status'] == 'Offboarded':
        continue
    cl_used = _r2.randint(0, 10)
    sl_used = _r2.randint(0, 10)
    el_used = _r2.randint(0, 15)
    leave_data.append({
        'id': e['id'], 'name': e['name'], 'geo': 'India', 'dept': e['dept'],
        'cl_entitled': 12, 'cl_used': cl_used, 'cl_balance': 12 - cl_used,
        'sl_entitled': 12, 'sl_used': sl_used, 'sl_balance': 12 - sl_used,
        'el_entitled': 18, 'el_used': el_used, 'el_balance': 18 - el_used,
        'attendance_pct': _r2.randint(88, 99) + _r2.random()
    })

for e in us_employees:
    if e['status'] == 'Offboarded':
        continue
    pto_used = _r2.randint(0, 12)
    sick_used = _r2.randint(0, 8)
    leave_data.append({
        'id': e['id'], 'name': e['name'], 'geo': 'US', 'dept': e['dept'],
        'cl_entitled': 15, 'cl_used': pto_used, 'cl_balance': 15 - pto_used,  # PTO
        'sl_entitled': 10, 'sl_used': sick_used, 'sl_balance': 10 - sick_used,
        'el_entitled': 0, 'el_used': 0, 'el_balance': 0,  # no EL in US
        'attendance_pct': _r2.randint(90, 99) + _r2.random()
    })

print(f"Leave data: {len(leave_data)} records")

# ----- PERFORMANCE GOALS DATA -----
goal_templates = [
    ('Revenue Target', 'Quarterly revenue achievement', '%'),
    ('Customer Satisfaction', 'CSAT score from surveys', 'score'),
    ('Product Quality', 'Defect rate reduction', '%'),
    ('Project Delivery', 'On-time project delivery', '%'),
    ('Skill Development', 'Certifications/courses completed', 'count'),
    ('Team Mentorship', 'Junior team members mentored', 'count'),
    ('Process Improvement', 'Process improvements implemented', 'count'),
    ('Cost Reduction', 'Cost savings achieved', '%'),
    ('Sales Pipeline', 'New deals added to pipeline', 'count'),
    ('Code Quality', 'Code review approval rate', '%'),
]

goals_data = []
goal_id_counter = 1
all_active = [(e, 'India') for e in india_employees if e['status'] != 'Offboarded'] + \
             [(e, 'US') for e in us_employees if e['status'] != 'Offboarded']

for e, geo in all_active:
    n_goals = _r2.randint(2, 4)
    chosen = _r2.sample(goal_templates, n_goals)
    for gt, gd, gu in chosen:
        target = _r2.choice([80, 90, 95, 100, 5, 10, 20]) if gu == '%' else _r2.randint(3, 10)
        achievement_pct = _r2.choices([100, 90, 80, 70, 60, 50, 40], weights=[15, 25, 25, 15, 10, 5, 5])[0]
        actual = round(target * achievement_pct / 100, 1)
        weight = _r2.choice([20, 25, 30, 40])
        # Rating: 5=>95%+, 4=>80-94, 3=>65-79, 2=>50-64, 1=<50
        if achievement_pct >= 95: rating = 5
        elif achievement_pct >= 80: rating = 4
        elif achievement_pct >= 65: rating = 3
        elif achievement_pct >= 50: rating = 2
        else: rating = 1
        goals_data.append({
            'goal_id': f'GL{goal_id_counter:04d}',
            'emp_id': e['id'], 'emp_name': e['name'], 'geo': geo, 'dept': e['dept'],
            'goal_title': gt, 'description': gd, 'unit': gu,
            'target': target, 'actual': actual, 'weight': weight,
            'achievement_pct': achievement_pct, 'rating': rating,
            'status': 'Completed' if achievement_pct >= 100 else ('On Track' if achievement_pct >= 70 else 'At Risk')
        })
        goal_id_counter += 1

print(f"Goals data: {len(goals_data)} records")

# ----- RECRUITMENT / ATS DATA -----
open_positions = [
    {'pos_id': 'JD-001', 'title': 'Senior Software Engineer', 'dept': 'Engineering', 'geo': 'India', 'openings': 3, 'priority': 'High', 'days_open': 18},
    {'pos_id': 'JD-002', 'title': 'Product Manager', 'dept': 'Product', 'geo': 'India', 'openings': 2, 'priority': 'High', 'days_open': 25},
    {'pos_id': 'JD-003', 'title': 'Data Scientist', 'dept': 'Engineering', 'geo': 'US', 'openings': 1, 'priority': 'Medium', 'days_open': 32},
    {'pos_id': 'JD-004', 'title': 'Sales Executive', 'dept': 'Sales', 'geo': 'India', 'openings': 4, 'priority': 'High', 'days_open': 12},
    {'pos_id': 'JD-005', 'title': 'Marketing Lead', 'dept': 'Marketing', 'geo': 'US', 'openings': 1, 'priority': 'Medium', 'days_open': 45},
    {'pos_id': 'JD-006', 'title': 'HR Business Partner', 'dept': 'HR', 'geo': 'India', 'openings': 1, 'priority': 'Low', 'days_open': 60},
    {'pos_id': 'JD-007', 'title': 'Customer Success Manager', 'dept': 'Customer Success', 'geo': 'India', 'openings': 2, 'priority': 'Medium', 'days_open': 22},
    {'pos_id': 'JD-008', 'title': 'DevOps Engineer', 'dept': 'Engineering', 'geo': 'US', 'openings': 1, 'priority': 'High', 'days_open': 8},
    {'pos_id': 'JD-009', 'title': 'Financial Analyst', 'dept': 'Finance', 'geo': 'India', 'openings': 1, 'priority': 'Low', 'days_open': 38},
    {'pos_id': 'JD-010', 'title': 'Operations Manager', 'dept': 'Operations', 'geo': 'India', 'openings': 1, 'priority': 'Medium', 'days_open': 27},
    {'pos_id': 'JD-011', 'title': 'UX Designer', 'dept': 'Product', 'geo': 'US', 'openings': 1, 'priority': 'Medium', 'days_open': 15},
    {'pos_id': 'JD-012', 'title': 'QA Engineer', 'dept': 'Engineering', 'geo': 'India', 'openings': 2, 'priority': 'High', 'days_open': 10},
]

# Candidate pipeline — distribute realistically
candidate_first_names = ['Rohit', 'Priya', 'Amit', 'Neha', 'Karan', 'Sneha', 'Vikram', 'Pooja',
                         'Rahul', 'Anjali', 'Sanjay', 'Riya', 'Manoj', 'Kavita', 'Arjun', 'Divya',
                         'Michael', 'Jennifer', 'David', 'Sarah', 'Robert', 'Lisa', 'James', 'Emily',
                         'Daniel', 'Jessica', 'Christopher', 'Amanda', 'Matthew', 'Rachel', 'Andrew', 'Megan']
candidate_last_names = ['Sharma', 'Verma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Joshi', 'Mehta',
                        'Smith', 'Johnson', 'Williams', 'Brown', 'Davis', 'Miller', 'Wilson', 'Moore']

candidates = []
cand_id_counter = 1
stages = ['Applied', 'Screened', 'Interviewed', 'Offered', 'Joined']
stage_weights = [40, 25, 18, 10, 7]  # funnel shape

for pos in open_positions:
    n_cands = _r2.randint(3, 8)
    for _ in range(n_cands):
        fn = _r2.choice(candidate_first_names)
        ln = _r2.choice(candidate_last_names)
        stage = _r2.choices(stages, weights=stage_weights)[0]
        days_in_stage = _r2.randint(2, 25)
        source = _r2.choice(['LinkedIn', 'Referral', 'Naukri', 'Indeed', 'Company Website', 'Recruiter'])
        candidates.append({
            'cand_id': f'CND-{cand_id_counter:04d}',
            'name': f'{fn} {ln}',
            'pos_id': pos['pos_id'],
            'pos_title': pos['title'],
            'dept': pos['dept'],
            'geo': pos['geo'],
            'stage': stage,
            'days_in_stage': days_in_stage,
            'source': source,
            'rating': _r2.randint(3, 5) if stage in ['Interviewed', 'Offered', 'Joined'] else 0
        })
        cand_id_counter += 1

print(f"Recruitment: {len(open_positions)} positions, {len(candidates)} candidates")

# ----- COMPLIANCE CALENDAR DATA -----
from datetime import timedelta as _td
_today = today
compliance_events = [
    {'comp_id': 'CMP-001', 'title': 'PF Monthly Filing (May 2026)', 'category': 'PF/EPF', 'geo': 'India', 'due_date': _today + _td(days=4), 'frequency': 'Monthly', 'authority': 'EPFO'},
    {'comp_id': 'CMP-002', 'title': 'ESI Monthly Contribution (May 2026)', 'category': 'ESI', 'geo': 'India', 'due_date': _today + _td(days=4), 'frequency': 'Monthly', 'authority': 'ESIC'},
    {'comp_id': 'CMP-003', 'title': 'TDS Deposit (Salary)', 'category': 'TDS', 'geo': 'India', 'due_date': _today - _td(days=4), 'frequency': 'Monthly', 'authority': 'Income Tax Dept'},
    {'comp_id': 'CMP-004', 'title': 'Professional Tax (Karnataka)', 'category': 'PT', 'geo': 'India', 'due_date': _today + _td(days=9), 'frequency': 'Monthly', 'authority': 'State Govt'},
    {'comp_id': 'CMP-005', 'title': 'Professional Tax (Maharashtra)', 'category': 'PT', 'geo': 'India', 'due_date': _today + _td(days=20), 'frequency': 'Monthly', 'authority': 'State Govt'},
    {'comp_id': 'CMP-006', 'title': 'Quarterly TDS Return (Q4 FY25-26)', 'category': 'TDS', 'geo': 'India', 'due_date': _today + _td(days=21), 'frequency': 'Quarterly', 'authority': 'Income Tax Dept'},
    {'comp_id': 'CMP-007', 'title': 'Form 16 Distribution to Employees', 'category': 'TDS', 'geo': 'India', 'due_date': _today + _td(days=45), 'frequency': 'Annual', 'authority': 'Income Tax Dept'},
    {'comp_id': 'CMP-008', 'title': 'Gratuity Payment - Resigned Employees', 'category': 'Gratuity', 'geo': 'India', 'due_date': _today + _td(days=12), 'frequency': 'As-needed', 'authority': 'Internal'},
    {'comp_id': 'CMP-009', 'title': 'Annual Return - Shops & Establishments', 'category': 'S&E Act', 'geo': 'India', 'due_date': _today + _td(days=60), 'frequency': 'Annual', 'authority': 'State Labour Dept'},
    {'comp_id': 'CMP-010', 'title': 'POSH Annual Report Filing', 'category': 'POSH', 'geo': 'India', 'due_date': _today + _td(days=85), 'frequency': 'Annual', 'authority': 'District Officer'},
    {'comp_id': 'CMP-011', 'title': 'Federal 941 Quarterly Filing', 'category': 'Federal Tax', 'geo': 'US', 'due_date': _today + _td(days=21), 'frequency': 'Quarterly', 'authority': 'IRS'},
    {'comp_id': 'CMP-012', 'title': 'State Unemployment Tax (SUTA)', 'category': 'State Tax', 'geo': 'US', 'due_date': _today + _td(days=15), 'frequency': 'Quarterly', 'authority': 'State'},
    {'comp_id': 'CMP-013', 'title': 'W-2 Forms to Employees', 'category': 'Federal Tax', 'geo': 'US', 'due_date': _today + _td(days=75), 'frequency': 'Annual', 'authority': 'IRS'},
    {'comp_id': 'CMP-014', 'title': 'I-9 Verification Audit', 'category': 'Immigration', 'geo': 'US', 'due_date': _today + _td(days=30), 'frequency': 'Quarterly', 'authority': 'USCIS'},
    {'comp_id': 'CMP-015', 'title': 'EEO-1 Report Filing', 'category': 'EEO', 'geo': 'US', 'due_date': _today + _td(days=55), 'frequency': 'Annual', 'authority': 'EEOC'},
    {'comp_id': 'CMP-016', 'title': 'Labour Welfare Fund', 'category': 'LWF', 'geo': 'India', 'due_date': _today + _td(days=42), 'frequency': 'Bi-Annual', 'authority': 'State Govt'},
    {'comp_id': 'CMP-017', 'title': 'Bonus Act Compliance Filing', 'category': 'Bonus Act', 'geo': 'India', 'due_date': _today + _td(days=120), 'frequency': 'Annual', 'authority': 'Labour Commissioner'},
    {'comp_id': 'CMP-018', 'title': 'ACA 1095-C Forms', 'category': 'Healthcare', 'geo': 'US', 'due_date': _today + _td(days=68), 'frequency': 'Annual', 'authority': 'IRS'},
]

# Assign status based on due date
for c in compliance_events:
    days_until = (c['due_date'] - _today).days
    if days_until < 0:
        c['status'] = 'Overdue'
    elif days_until <= 7:
        c['status'] = 'Critical'
    elif days_until <= 30:
        c['status'] = 'Upcoming'
    else:
        c['status'] = 'Scheduled'

print(f"Compliance: {len(compliance_events)} events")

# ----- TRAINING & DEVELOPMENT DATA -----
training_programs = [
    {'train_id': 'TRN-001', 'title': 'Leadership Excellence Program', 'category': 'Leadership', 'duration_hrs': 40, 'mandatory': False, 'target': 'Manager+'},
    {'train_id': 'TRN-002', 'title': 'Workplace Safety & POSH', 'category': 'Compliance', 'duration_hrs': 4, 'mandatory': True, 'target': 'All Employees'},
    {'train_id': 'TRN-003', 'title': 'Cloud Computing - AWS Foundation', 'category': 'Technical', 'duration_hrs': 24, 'mandatory': False, 'target': 'Engineering'},
    {'train_id': 'TRN-004', 'title': 'Customer Communication Skills', 'category': 'Soft Skills', 'duration_hrs': 16, 'mandatory': False, 'target': 'Customer-facing'},
    {'train_id': 'TRN-005', 'title': 'Data Privacy & GDPR', 'category': 'Compliance', 'duration_hrs': 6, 'mandatory': True, 'target': 'All Employees'},
    {'train_id': 'TRN-006', 'title': 'Sales Negotiation Mastery', 'category': 'Sales', 'duration_hrs': 20, 'mandatory': False, 'target': 'Sales Team'},
    {'train_id': 'TRN-007', 'title': 'Agile & Scrum Certification', 'category': 'Methodology', 'duration_hrs': 32, 'mandatory': False, 'target': 'Engineering/Product'},
    {'train_id': 'TRN-008', 'title': 'Diversity & Inclusion Workshop', 'category': 'Culture', 'duration_hrs': 8, 'mandatory': True, 'target': 'All Employees'},
]

# Training enrollments — each employee enrolled in ~2-4 programs
training_enrollments = []
enroll_id = 1
for e, geo in all_active:
    n = _r2.randint(2, 4)
    # mandatory programs first (always assigned)
    mandatory_ids = [t['train_id'] for t in training_programs if t['mandatory']]
    optional_ids = [t['train_id'] for t in training_programs if not t['mandatory']]
    assigned = list(mandatory_ids) + _r2.sample(optional_ids, min(n, len(optional_ids)))
    for tid in assigned:
        completion = _r2.choices([100, 100, 100, 75, 50, 25, 0], weights=[35, 20, 15, 10, 8, 7, 5])[0]
        prog = next(p for p in training_programs if p['train_id'] == tid)
        if completion == 100:
            status = 'Completed'
        elif completion >= 50:
            status = 'In Progress'
        else:
            status = 'Not Started'
        training_enrollments.append({
            'enroll_id': f'ENR-{enroll_id:04d}',
            'emp_id': e['id'], 'emp_name': e['name'], 'geo': geo, 'dept': e['dept'],
            'train_id': tid, 'train_title': prog['title'], 'category': prog['category'],
            'mandatory': prog['mandatory'], 'completion_pct': completion, 'status': status
        })
        enroll_id += 1

print(f"Training: {len(training_programs)} programs, {len(training_enrollments)} enrollments")

# ----- ATTRITION RISK SCORES -----
# Risk score = weighted formula based on tenure, productivity, comp ratio, recent manager change
attrition_risk = []
for e, geo in all_active:
    # Tenure factor (lower tenure = higher risk for first 18 months, then drops)
    tenure_days = (_today - e['doj']).days
    if tenure_days < 180:
        tenure_score = 50  # very new
    elif tenure_days < 540:
        tenure_score = 30  # 6-18 months — common attrition window
    elif tenure_days < 1080:
        tenure_score = 15
    else:
        tenure_score = 8

    # Productivity factor (look up from productivity_data)
    prod_rec = next((p for p in productivity_data if p['id'] == e['id']), None)
    prod_score = 0
    if prod_rec:
        if prod_rec['score'] <= 2:
            prod_score = 35
        elif prod_rec['score'] == 3:
            prod_score = 18
        elif prod_rec['score'] == 4:
            prod_score = 8
        else:
            prod_score = 3

    # Comp ratio - simulate (some employees underpaid for their band)
    comp_score = _r2.choices([20, 10, 5, 0], weights=[15, 25, 35, 25])[0]

    # Other factors
    other_score = _r2.choices([15, 10, 5, 0], weights=[10, 20, 30, 40])[0]

    total = tenure_score + prod_score + comp_score + other_score
    total = min(100, total)

    if total >= 65:
        risk_level = 'High'
    elif total >= 35:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    # Top reason
    factors = [('Low Productivity', prod_score), ('Below Market Comp', comp_score),
               ('Early Tenure', tenure_score), ('Other Factors', other_score)]
    factors.sort(key=lambda x: -x[1])
    top_reason = factors[0][0]

    attrition_risk.append({
        'id': e['id'], 'name': e['name'], 'geo': geo, 'dept': e['dept'],
        'desig': e['desig'], 'manager': e['manager'],
        'tenure_days': tenure_days,
        'tenure_score': tenure_score, 'prod_score': prod_score,
        'comp_score': comp_score, 'other_score': other_score,
        'total_score': total, 'risk_level': risk_level, 'top_reason': top_reason
    })

# Sort by risk score descending
attrition_risk.sort(key=lambda x: -x['total_score'])
print(f"Attrition risk: {len(attrition_risk)} employees scored")
print(f"  High risk: {sum(1 for r in attrition_risk if r['risk_level'] == 'High')}")
print(f"  Medium risk: {sum(1 for r in attrition_risk if r['risk_level'] == 'Medium')}")
print(f"  Low risk: {sum(1 for r in attrition_risk if r['risk_level'] == 'Low')}")
