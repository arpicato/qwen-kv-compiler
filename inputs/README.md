# Frozen publication inputs

All prerequisites to the reproduction are tracked here. No binary teacher state,
captures, projections or fitted cache are inputs. Those are regenerated from the
explicit external model/runtime. Generated outputs go outside this directory.

`joint/`: exact26341tokenprompt,812Q/A,48+24sampling,24behaviorcases,
78fixed/197stressprobes,40offline tasks with unchanged transport/acceptance.
`continuation/`:64newtrain-onlyQ/A and their frozen token/query-position plan.
File bytes were copied from the completed experiments, not repaired after scoring.
`manifest.json` contains relative paths/SHA256/bytes for every input file.

Calibration includes authored teacher-forced answers, not proof the full model
freely generates those answers. Query selector for the812 is the legacy selector;
the64newcontinuationexamples have explicit positions. Policy evaluation cases
are disjoint in exact question text, not independent semantic families.

Third-party tool descriptions/agent instruction text keep the notices in
`THIRD_PARTY_NOTICES.md`. Original tasks/annotations are MIT-0; embedded upstream
material retains its own terms. No weights or credentials are included.
