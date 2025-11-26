# Reports

Generated reports and report generation scripts.

## Structure

- `enhanced_report_generator.py` - Main report generation script
- `daily/` - Daily generated reports
- `weekly/` - Weekly summary reports

## Generating Reports

```bash
make report          # Generate daily report
make weekly-report   # Generate weekly proposal report
```

## Report Types

| Report | Frequency | Description |
|--------|-----------|-------------|
| Brain Report | Daily | System activity and status |
| Proposal Report | Weekly | Proposal pipeline summary |

## Output

Reports are typically saved as HTML files in subdirectories.
