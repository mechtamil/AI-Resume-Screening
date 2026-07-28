# RecruitOS Master Data

`RecruitOS_Configuration.xlsx` is the **single authoritative configuration/master-data workbook**.

Do not recreate separate `skills_master.xlsx`, `education_master.xlsx`, `certification_master.xlsx`, or `scoring_master.xlsx` files.

Required sheets and structural columns are defined in `config/sheet_names.py`.

To create a new empty template from the project root:

```powershell
python -m tools.create_configuration_workbook
```

The generator refuses to overwrite an existing workbook. `--force` creates a timestamped backup before replacement.

Business values must be maintained in the workbook, not hardcoded in Python.
