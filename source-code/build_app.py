"""Assemble the HR portal HTML from template + JSON data + inlined Chart.js."""
with open('/home/claude/hr_data.json') as f:
    data_json = f.read()

with open('/home/claude/hr_app/chart.umd.js') as f:
    chartjs = f.read()

with open('/home/claude/hr_app/template.html') as f:
    template = f.read()

# Replace CDN script tag with inlined Chart.js
cdn_tag = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>'
inline_tag = '<script>/* Chart.js v4.4.0 (inlined for offline) */\n' + chartjs + '\n</script>'
output = template.replace(cdn_tag, inline_tag)

# Inject data
output = output.replace('/*__DATA_PLACEHOLDER__*/null', data_json)

out_path = '/home/claude/hr_app/HR_Portal.html'
with open(out_path, 'w') as f:
    f.write(output)

print(f"Built: {out_path}")
print(f"Size: {len(output):,} bytes ({len(output)/1024:.1f} KB)")
